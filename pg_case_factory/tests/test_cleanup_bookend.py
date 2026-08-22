"""TDD red tests for the shared ``cleanup_bookend`` helper.

The helper encodes the ``alter_sequence`` good idiom as a safe-by-construction
builder so that **bare DROPs and pre-cleanup ``DROP OWNED BY`` are impossible to
construct**. These tests assert the exact emission contract before any
implementation exists; they fail until ``cleanup_bookend.py`` lands.
"""

from __future__ import annotations

import unittest
from dataclasses import FrozenInstanceError

from pg_case_factory.cleanup_bookend import (
    CLEANUP_BEGIN,
    CLEANUP_END,
    PRE_CLEANUP_BEGIN,
    PRE_CLEANUP_END,
    CleanupBookend,
    DropSpec,
    build_cleanup,
    build_pre_cleanup,
    guarded_drop_owned_by,
    guarded_drop_role,
    idempotent_drop,
)


class TestIdempotentDrop(unittest.TestCase):
    """Every DROP must carry IF EXISTS and an object kind from the allowlist."""

    def test_aggregate_with_args_emits_cascade(self) -> None:
        self.assertEqual(
            idempotent_drop(DropSpec("AGGREGATE", "foo", "(int)")),
            "DROP AGGREGATE IF EXISTS foo(int) CASCADE;",
        )

    def test_function_no_cascade_omits_suffix(self) -> None:
        self.assertEqual(
            idempotent_drop(DropSpec("FUNCTION", "bar", "(int,int)", cascade=False)),
            "DROP FUNCTION IF EXISTS bar(int,int);",
        )

    def test_schema_no_args_defaults_cascade(self) -> None:
        self.assertEqual(
            idempotent_drop(DropSpec("SCHEMA", "baz")),
            "DROP SCHEMA IF EXISTS baz CASCADE;",
        )

    def test_materialized_view_kind_with_space(self) -> None:
        self.assertEqual(
            idempotent_drop(DropSpec("MATERIALIZED VIEW", "mv")),
            "DROP MATERIALIZED VIEW IF EXISTS mv CASCADE;",
        )

    def test_qualified_identifier_preserved(self) -> None:
        self.assertEqual(
            idempotent_drop(DropSpec("TABLE", "public.foo")),
            "DROP TABLE IF EXISTS public.foo CASCADE;",
        )

    def test_database_kind_rejected(self) -> None:
        with self.assertRaises(ValueError):
            idempotent_drop(DropSpec("DATABASE", "x"))

    def test_role_kind_rejected_drop_role_has_no_cascade(self) -> None:
        # DROP ROLE does not accept CASCADE; roles go through guarded_drop_role.
        with self.assertRaises(ValueError):
            idempotent_drop(DropSpec("ROLE", "r"))

    def test_invalid_identifier_rejected(self) -> None:
        for bad in ("'inj'", "a; DROP x", "col--x", "a b", ""):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    idempotent_drop(DropSpec("AGGREGATE", bad, "(int)"))

    def test_quoted_identifier_accepted(self) -> None:
        # Quoted identifiers (reserved-word/spaced names used by renders like
        # create_aggregate) are legitimate and safe: ';' inside "..." is literal.
        self.assertEqual(
            idempotent_drop(
                DropSpec("AGGREGATE", '"createaggregate_00010_Mixed Agg"', "(int)")
            ),
            'DROP AGGREGATE IF EXISTS "createaggregate_00010_Mixed Agg"(int) CASCADE;',
        )
        self.assertEqual(
            idempotent_drop(DropSpec("TABLE", '"q"')),
            'DROP TABLE IF EXISTS "q" CASCADE;',
        )

    def test_malformed_quoted_identifier_rejected(self) -> None:
        for bad in ('"q', 'q"', '"a"b"', '"a"b'):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    idempotent_drop(DropSpec("AGGREGATE", bad, "(int)"))

    def test_args_with_semicolon_rejected(self) -> None:
        with self.assertRaises(ValueError):
            idempotent_drop(DropSpec("FUNCTION", "foo", "(int); DROP x"))


class TestStandardSyntaxKinds(unittest.TestCase):
    """Kinds whose DROP syntax is the plain ``DROP <KIND> IF EXISTS name CASCADE``.

    These kinds (CONVERSION, ACCESS METHOD, EVENT TRIGGER, and the four
    TEXT SEARCH object kinds) take a single name identifier and no ON/USING/
    signature clause, so they fit the existing ``idempotent_drop`` template
    without new fields. They were blocked in batch-2 because they were absent
    from ``_DROP_KINDS``.
    """

    _STANDARD_KINDS: tuple[str, ...] = (
        "ACCESS METHOD",
        "CONVERSION",
        "EVENT TRIGGER",
        "FOREIGN DATA WRAPPER",
        "FOREIGN TABLE",
        "SERVER",
        "TEXT SEARCH CONFIGURATION",
        "TEXT SEARCH DICTIONARY",
        "TEXT SEARCH PARSER",
        "TEXT SEARCH TEMPLATE",
    )

    def test_each_standard_kind_emits_cascade_drop(self) -> None:
        for kind in self._STANDARD_KINDS:
            with self.subTest(kind=kind):
                self.assertEqual(
                    idempotent_drop(DropSpec(kind, "obj")),
                    f"DROP {kind} IF EXISTS obj CASCADE;",
                )

    def test_each_standard_kind_in_drop_kinds(self) -> None:
        for kind in self._STANDARD_KINDS:
            with self.subTest(kind=kind):
                bookend = build_pre_cleanup(specs=(DropSpec(kind, "obj"),))
                self.assertEqual(bookend.drop_kinds, (kind,))

    def test_text_search_configuration_qualified_name(self) -> None:
        self.assertEqual(
            idempotent_drop(DropSpec("TEXT SEARCH CONFIGURATION", "public.my_cfg")),
            "DROP TEXT SEARCH CONFIGURATION IF EXISTS public.my_cfg CASCADE;",
        )

    def test_access_method_no_cascade_omits_suffix(self) -> None:
        self.assertEqual(
            idempotent_drop(DropSpec("ACCESS METHOD", "am", cascade=False)),
            "DROP ACCESS METHOD IF EXISTS am;",
        )


class TestGuardedDropOwnedBy(unittest.TestCase):
    def test_emits_cascade(self) -> None:
        self.assertEqual(guarded_drop_owned_by("r"), "DROP OWNED BY r CASCADE;")

    def test_invalid_role_rejected(self) -> None:
        with self.assertRaises(ValueError):
            guarded_drop_owned_by("r; DROP x")


class TestGuardedDropRole(unittest.TestCase):
    def test_emits_if_exists_no_cascade(self) -> None:
        self.assertEqual(guarded_drop_role("r"), "DROP ROLE IF EXISTS r;")

    def test_invalid_role_rejected(self) -> None:
        with self.assertRaises(ValueError):
            guarded_drop_role("'inj'")


class TestBuildPreCleanup(unittest.TestCase):
    def test_empty_emits_residual_select(self) -> None:
        bookend = build_pre_cleanup()
        self.assertEqual(
            bookend.statements,
            (PRE_CLEANUP_BEGIN, "SELECT 1 AS residual_check_no_objects;", PRE_CLEANUP_END),
        )

    def test_tables_first_and_cascade(self) -> None:
        bookend = build_pre_cleanup(tables=("t1", "t2"))
        self.assertEqual(
            bookend.statements,
            (PRE_CLEANUP_BEGIN, "DROP TABLE IF EXISTS t1, t2 CASCADE;", PRE_CLEANUP_END),
        )
        self.assertEqual(bookend.drop_kinds, ("TABLE",))

    def test_specs_in_caller_order(self) -> None:
        bookend = build_pre_cleanup(
            specs=(DropSpec("AGGREGATE", "a", "(int)"), DropSpec("FUNCTION", "f", "(int)"))
        )
        self.assertEqual(
            bookend.statements,
            (
                PRE_CLEANUP_BEGIN,
                "DROP AGGREGATE IF EXISTS a(int) CASCADE;",
                "DROP FUNCTION IF EXISTS f(int) CASCADE;",
                PRE_CLEANUP_END,
            ),
        )
        self.assertEqual(bookend.drop_kinds, ("AGGREGATE", "FUNCTION"))

    def test_roles_use_drop_role_if_exists_only(self) -> None:
        # pre-cleanup MUST NOT emit DROP OWNED BY (role may not own objects yet).
        bookend = build_pre_cleanup(roles=("r1", "r2"))
        self.assertEqual(
            bookend.statements,
            (
                PRE_CLEANUP_BEGIN,
                "DROP ROLE IF EXISTS r1;",
                "DROP ROLE IF EXISTS r2;",
                PRE_CLEANUP_END,
            ),
        )
        for stmt in bookend.statements:
            self.assertNotIn("DROP OWNED BY", stmt)

    def test_combined_order_tables_specs_schemas_roles(self) -> None:
        bookend = build_pre_cleanup(
            tables=("t",),
            specs=(DropSpec("SEQUENCE", "s"),),
            schemas=("sch",),
            roles=("r",),
        )
        self.assertEqual(
            bookend.statements,
            (
                PRE_CLEANUP_BEGIN,
                "DROP TABLE IF EXISTS t CASCADE;",
                "DROP SEQUENCE IF EXISTS s CASCADE;",
                "DROP SCHEMA IF EXISTS sch CASCADE;",
                "DROP ROLE IF EXISTS r;",
                PRE_CLEANUP_END,
            ),
        )

    def test_no_drop_owned_by_reachable_in_pre_cleanup(self) -> None:
        # No combination of public pre-cleanup kwargs may produce DROP OWNED BY.
        bookend = build_pre_cleanup(
            tables=("t",), specs=(DropSpec("SEQUENCE", "s"),), schemas=("sch",), roles=("r",)
        )
        for stmt in bookend.statements:
            self.assertNotIn("DROP OWNED BY", stmt)


class TestBuildCleanup(unittest.TestCase):
    def test_empty_emits_residual_select(self) -> None:
        bookend = build_cleanup()
        self.assertEqual(
            bookend.statements,
            (CLEANUP_BEGIN, "SELECT 1 AS residual_check_no_objects;", CLEANUP_END),
        )

    def test_drop_owned_before_drop_role(self) -> None:
        bookend = build_cleanup(roles=("r",), drop_owned=True)
        self.assertEqual(
            bookend.statements,
            (
                CLEANUP_BEGIN,
                "DROP OWNED BY r CASCADE;",
                "DROP ROLE IF EXISTS r;",
                CLEANUP_END,
            ),
        )

    def test_drop_owned_false_omits_drop_owned(self) -> None:
        bookend = build_cleanup(roles=("r",), drop_owned=False)
        self.assertEqual(
            bookend.statements,
            (CLEANUP_BEGIN, "DROP ROLE IF EXISTS r;", CLEANUP_END),
        )

    def test_tables_are_last_anchor(self) -> None:
        bookend = build_cleanup(
            roles=("r",), drop_owned=True, tables=("t",)
        )
        self.assertEqual(
            bookend.statements,
            (
                CLEANUP_BEGIN,
                "DROP OWNED BY r CASCADE;",
                "DROP ROLE IF EXISTS r;",
                "DROP TABLE IF EXISTS t CASCADE;",
                CLEANUP_END,
            ),
        )
        # The anchor DROP TABLE is the last executable line before the end marker.
        self.assertEqual(bookend.statements[-2], "DROP TABLE IF EXISTS t CASCADE;")

    def test_reset_role_first_when_requested(self) -> None:
        bookend = build_cleanup(reset_role=True, roles=("r",), drop_owned=True)
        self.assertEqual(bookend.statements[1], "RESET ROLE;")

    def test_schemas_before_roles(self) -> None:
        bookend = build_cleanup(schemas=("sch",), roles=("r",), drop_owned=True)
        self.assertLess(
            bookend.statements.index("DROP SCHEMA IF EXISTS sch CASCADE;"),
            bookend.statements.index("DROP OWNED BY r CASCADE;"),
        )


class TestImmutability(unittest.TestCase):
    def test_drop_spec_frozen(self) -> None:
        spec = DropSpec("AGGREGATE", "foo", "(int)")
        with self.assertRaises(FrozenInstanceError):
            spec.kind = "FUNCTION"  # type: ignore[misc]

    def test_cleanup_bookend_statements_frozen(self) -> None:
        bookend = build_pre_cleanup(tables=("t",))
        with self.assertRaises(FrozenInstanceError):
            bookend.statements = ("x",)  # type: ignore[misc]

    def test_statements_is_tuple_not_list(self) -> None:
        bookend = build_pre_cleanup(tables=("t",))
        self.assertIsInstance(bookend.statements, tuple)
        self.assertIsInstance(bookend.drop_kinds, tuple)


if __name__ == "__main__":
    unittest.main()
