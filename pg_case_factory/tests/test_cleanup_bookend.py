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
    CastDropSpec,
    CleanupBookend,
    DropSpec,
    OnDropSpec,
    TransformDropSpec,
    UserMappingDropSpec,
    UsingDropSpec,
    build_cleanup,
    build_pre_cleanup,
    guarded_drop_owned_by,
    guarded_drop_role,
    idempotent_drop,
    idempotent_drop_cast,
    idempotent_drop_on,
    idempotent_drop_transform,
    idempotent_drop_using,
    idempotent_drop_user_mapping,
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
        "PUBLICATION",
        "ROUTINE",
        "SERVER",
        "STATISTICS",
        "SUBSCRIPTION",
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


class TestComplexKinds(unittest.TestCase):
    """Complex DROP clause shapes (A-E) that ``idempotent_drop`` cannot express.

    These kinds need an ``ON <table>``, ``USING <method>``, ``(src AS tgt)``,
    ``FOR <type> LANGUAGE <lang>``, or ``FOR <user> SERVER <server>`` clause and
    so get dedicated frozen specs + builders that mirror ``idempotent_drop``'s
    safe-by-construction style. ``ROUTINE`` is plain standard syntax and is
    covered by ``TestStandardSyntaxKinds`` (just an allowlist add).
    """

    # --- Shape A: ON <table> (TRIGGER / RULE / POLICY) ---
    def test_trigger_on_table_cascade(self) -> None:
        self.assertEqual(
            idempotent_drop_on(OnDropSpec("TRIGGER", "trg", "tbl")),
            "DROP TRIGGER IF EXISTS trg ON tbl CASCADE;",
        )

    def test_rule_on_view_no_cascade(self) -> None:
        self.assertEqual(
            idempotent_drop_on(OnDropSpec("RULE", "rl", "v", cascade=False)),
            "DROP RULE IF EXISTS rl ON v;",
        )

    def test_policy_on_table_cascade(self) -> None:
        self.assertEqual(
            idempotent_drop_on(OnDropSpec("POLICY", "p", "t")),
            "DROP POLICY IF EXISTS p ON t CASCADE;",
        )

    # --- Shape B: USING <method> (OPERATOR CLASS / OPERATOR FAMILY) ---
    def test_operator_class_using_btree_cascade(self) -> None:
        self.assertEqual(
            idempotent_drop_using(UsingDropSpec("OPERATOR CLASS", "opc", "btree")),
            "DROP OPERATOR CLASS IF EXISTS opc USING btree CASCADE;",
        )

    def test_operator_family_using_gin_no_cascade(self) -> None:
        self.assertEqual(
            idempotent_drop_using(
                UsingDropSpec("OPERATOR FAMILY", "opf", "gin", cascade=False)
            ),
            "DROP OPERATOR FAMILY IF EXISTS opf USING gin;",
        )

    # --- Shape C: CAST (no name; (src AS tgt)) ---
    def test_cast_src_to_tgt_cascade(self) -> None:
        self.assertEqual(
            idempotent_drop_cast(CastDropSpec("int4", "text")),
            "DROP CAST IF EXISTS (int4 AS text) CASCADE;",
        )

    # --- Shape D: TRANSFORM (no name; FOR <type> LANGUAGE <lang>) ---
    def test_transform_for_type_language_cascade(self) -> None:
        self.assertEqual(
            idempotent_drop_transform(TransformDropSpec("mytype", "plpgsql")),
            "DROP TRANSFORM IF EXISTS FOR mytype LANGUAGE plpgsql CASCADE;",
        )

    # --- Shape E: USER MAPPING (no name; FOR <user> SERVER <server>) ---
    # NOTE: DROP USER MAPPING has no CASCADE/RESTRICT clause in PG18 (it owns no
    # dependent objects), so UserMappingDropSpec carries no cascade field and the
    # builder never appends a suffix.
    def test_user_mapping_actor_server(self) -> None:
        self.assertEqual(
            idempotent_drop_user_mapping(UserMappingDropSpec("actor", "srv")),
            "DROP USER MAPPING IF EXISTS FOR actor SERVER srv;",
        )

    def test_user_mapping_public_server(self) -> None:
        # PUBLIC is a valid (special) user for shape E.
        self.assertEqual(
            idempotent_drop_user_mapping(UserMappingDropSpec("PUBLIC", "srv")),
            "DROP USER MAPPING IF EXISTS FOR PUBLIC SERVER srv;",
        )

    def test_user_mapping_never_emits_cascade_or_restrict(self) -> None:
        # Regression: the builder must never append CASCADE/RESTRICT regardless of
        # how the spec is built — DROP USER MAPPING has no such clause in PG18.
        out = idempotent_drop_user_mapping(UserMappingDropSpec("actor", "srv"))
        self.assertNotIn("CASCADE", out)
        self.assertNotIn("RESTRICT", out)

    # --- Rejection: empty fields ---
    def test_empty_on_rejected(self) -> None:
        with self.assertRaises(ValueError):
            idempotent_drop_on(OnDropSpec("TRIGGER", "trg", ""))

    def test_empty_using_rejected(self) -> None:
        with self.assertRaises(ValueError):
            idempotent_drop_using(UsingDropSpec("OPERATOR CLASS", "opc", ""))

    def test_empty_cast_src_tgt_rejected(self) -> None:
        with self.assertRaises(ValueError):
            idempotent_drop_cast(CastDropSpec("", "text"))
        with self.assertRaises(ValueError):
            idempotent_drop_cast(CastDropSpec("int4", ""))

    def test_empty_transform_type_lang_rejected(self) -> None:
        with self.assertRaises(ValueError):
            idempotent_drop_transform(TransformDropSpec("", "plpgsql"))
        with self.assertRaises(ValueError):
            idempotent_drop_transform(TransformDropSpec("mytype", ""))

    def test_empty_user_mapping_user_server_rejected(self) -> None:
        with self.assertRaises(ValueError):
            idempotent_drop_user_mapping(UserMappingDropSpec("", "srv"))
        with self.assertRaises(ValueError):
            idempotent_drop_user_mapping(UserMappingDropSpec("actor", ""))

    # --- Rejection: non-allowlist kind ---
    def test_on_drop_non_allowlist_kind_rejected(self) -> None:
        # TABLE is a standard kind but not an ON-clause kind -> rejected by the
        # ON builder (it must go through idempotent_drop, not idempotent_drop_on).
        with self.assertRaises(ValueError):
            idempotent_drop_on(OnDropSpec("TABLE", "t", "tbl"))

    def test_using_drop_non_allowlist_kind_rejected(self) -> None:
        with self.assertRaises(ValueError):
            idempotent_drop_using(UsingDropSpec("SERVER", "s", "btree"))

    # --- Rejection: injection / malformed identifiers ---
    def test_on_table_injection_rejected(self) -> None:
        with self.assertRaises(ValueError):
            idempotent_drop_on(OnDropSpec("TRIGGER", "trg", "tbl; DROP x"))

    def test_using_method_injection_rejected(self) -> None:
        with self.assertRaises(ValueError):
            idempotent_drop_using(UsingDropSpec("OPERATOR CLASS", "opc", "btree; DROP x"))

    def test_user_mapping_server_injection_rejected(self) -> None:
        with self.assertRaises(ValueError):
            idempotent_drop_user_mapping(UserMappingDropSpec("actor", "srv; DROP x"))

    # --- Frozen dataclasses ---
    def test_on_drop_spec_frozen(self) -> None:
        spec = OnDropSpec("TRIGGER", "trg", "tbl")
        with self.assertRaises(FrozenInstanceError):
            spec.kind = "RULE"  # type: ignore[misc]

    def test_using_drop_spec_frozen(self) -> None:
        spec = UsingDropSpec("OPERATOR CLASS", "opc", "btree")
        with self.assertRaises(FrozenInstanceError):
            spec.using = "hash"  # type: ignore[misc]

    def test_cast_drop_spec_frozen(self) -> None:
        spec = CastDropSpec("int4", "text")
        with self.assertRaises(FrozenInstanceError):
            spec.src = "int8"  # type: ignore[misc]

    def test_transform_drop_spec_frozen(self) -> None:
        spec = TransformDropSpec("mytype", "plpgsql")
        with self.assertRaises(FrozenInstanceError):
            spec.lang = "sql"  # type: ignore[misc]

    def test_user_mapping_drop_spec_frozen(self) -> None:
        spec = UserMappingDropSpec("actor", "srv")
        with self.assertRaises(FrozenInstanceError):
            spec.server = "s2"  # type: ignore[misc]

    # --- complex_specs plumbing ---
    def test_complex_specs_plumbing_pre_cleanup(self) -> None:
        bookend = build_pre_cleanup(complex_specs=(OnDropSpec("TRIGGER", "trg", "tbl"),))
        self.assertIn("DROP TRIGGER IF EXISTS trg ON tbl CASCADE;", bookend.statements)
        self.assertIn("TRIGGER", bookend.drop_kinds)

    def test_complex_specs_plumbing_cleanup(self) -> None:
        bookend = build_cleanup(complex_specs=(OnDropSpec("POLICY", "p", "t"),))
        self.assertIn("DROP POLICY IF EXISTS p ON t CASCADE;", bookend.statements)
        self.assertIn("POLICY", bookend.drop_kinds)

    def test_complex_specs_after_specs_before_schemas_pre_cleanup(self) -> None:
        bookend = build_pre_cleanup(
            specs=(DropSpec("SEQUENCE", "s"),),
            complex_specs=(OnDropSpec("TRIGGER", "trg", "tbl"),),
            schemas=("sch",),
        )
        stmts = bookend.statements
        seq_i = stmts.index("DROP SEQUENCE IF EXISTS s CASCADE;")
        trg_i = stmts.index("DROP TRIGGER IF EXISTS trg ON tbl CASCADE;")
        sch_i = stmts.index("DROP SCHEMA IF EXISTS sch CASCADE;")
        self.assertLess(seq_i, trg_i)
        self.assertLess(trg_i, sch_i)

    def test_complex_specs_after_specs_before_schemas_cleanup(self) -> None:
        bookend = build_cleanup(
            specs=(DropSpec("SEQUENCE", "s"),),
            complex_specs=(OnDropSpec("TRIGGER", "trg", "tbl"),),
            schemas=("sch",),
        )
        stmts = bookend.statements
        seq_i = stmts.index("DROP SEQUENCE IF EXISTS s CASCADE;")
        trg_i = stmts.index("DROP TRIGGER IF EXISTS trg ON tbl CASCADE;")
        sch_i = stmts.index("DROP SCHEMA IF EXISTS sch CASCADE;")
        self.assertLess(seq_i, trg_i)
        self.assertLess(trg_i, sch_i)

    def test_complex_specs_multiple_shapes_dispatched(self) -> None:
        bookend = build_pre_cleanup(
            complex_specs=(
                OnDropSpec("TRIGGER", "trg", "tbl"),
                UsingDropSpec("OPERATOR CLASS", "opc", "btree"),
                CastDropSpec("int4", "text"),
                TransformDropSpec("mytype", "plpgsql"),
                UserMappingDropSpec("actor", "srv"),
            )
        )
        self.assertIn("DROP TRIGGER IF EXISTS trg ON tbl CASCADE;", bookend.statements)
        self.assertIn("DROP OPERATOR CLASS IF EXISTS opc USING btree CASCADE;", bookend.statements)
        self.assertIn("DROP CAST IF EXISTS (int4 AS text) CASCADE;", bookend.statements)
        self.assertIn(
            "DROP TRANSFORM IF EXISTS FOR mytype LANGUAGE plpgsql CASCADE;", bookend.statements
        )
        self.assertIn(
            "DROP USER MAPPING IF EXISTS FOR actor SERVER srv;", bookend.statements
        )
        self.assertEqual(
            bookend.drop_kinds,
            ("TRIGGER", "OPERATOR CLASS", "CAST", "TRANSFORM", "USER MAPPING"),
        )


if __name__ == "__main__":
    unittest.main()
