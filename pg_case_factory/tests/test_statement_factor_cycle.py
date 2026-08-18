from __future__ import annotations

import hashlib
import json
from pathlib import Path
import re
import tempfile
import unittest

import yaml

from pg_case_factory.statement_factor_cycle import (
    StatementFactorCycleError,
    complete_cycle_statement,
    discover_statement_factor_cycle,
    initialize_cycle_state,
    materialize_cycle_documents,
    render_cycle_plan_markdown,
    render_factor_inventory_markdown,
)


ROOT = Path(__file__).resolve().parents[1]


class StatementFactorCycleDiscoveryTest(unittest.TestCase):
    def test_discovers_exact_remaining_statement_and_factor_universe(self) -> None:
        snapshot = discover_statement_factor_cycle(ROOT)

        self.assertEqual(183, snapshot.statement_count)
        self.assertEqual(3357, snapshot.factor_count)
        self.assertEqual(9978, snapshot.factor_value_count)
        self.assertEqual(6, snapshot.retained_statement_count)
        self.assertEqual(177, snapshot.pending_statement_count)
        self.assertEqual(3277, snapshot.pending_factor_count)
        self.assertEqual(9676, snapshot.pending_factor_value_count)
        self.assertEqual(10, snapshot.pg18_compatibility_value_count)
        self.assertEqual(10, snapshot.pending_pg18_compatibility_value_count)
        self.assertEqual("abort", snapshot.pending_entries[0].statement_key)
        self.assertEqual(
            {"close", "declare", "fetch", "move", "grant", "revoke"},
            {entry.statement_key for entry in snapshot.retained_entries},
        )
        inventory = yaml.safe_load(
            (
                ROOT
                / "skills/pg-sql-generation/references/common/statement_support_inventory.yaml"
            ).read_text(encoding="utf-8")
        )
        self.assertEqual(
            tuple(row["statement_key"] for row in inventory["statements"]),
            tuple(entry.statement_key for entry in snapshot.entries),
        )

    def test_every_statement_has_one_matrix_and_matching_reference_counts(self) -> None:
        snapshot = discover_statement_factor_cycle(ROOT)

        self.assertEqual(
            snapshot.statement_count,
            len({entry.matrix_path for entry in snapshot.entries}),
        )
        for entry in snapshot.entries:
            self.assertTrue((ROOT / entry.matrix_path).is_file(), entry.statement_key)
            self.assertTrue((ROOT / entry.reference_path).is_file(), entry.statement_key)
            self.assertRegex(entry.matrix_sha256, r"^[0-9a-f]{64}$")
            self.assertRegex(entry.reference_sha256, r"^[0-9a-f]{64}$")
            self.assertEqual(entry.factor_count, len(entry.factors))
            self.assertEqual(
                entry.factor_value_count,
                sum(len(factor.values) for factor in entry.factors),
            )

    def test_exactly_ten_canonical_values_use_pg18_compatibility_witnesses(self) -> None:
        snapshot = discover_statement_factor_cycle(ROOT)
        bindings = [
            (entry.statement_key, factor.name, value, binding)
            for entry in snapshot.entries
            for factor in entry.factors
            for value, binding in zip(factor.values, factor.matrix_bindings)
            if binding == "pg18_compatibility"
        ]

        self.assertEqual(10, len(bindings))
        self.assertIn(
            ("insert", "result_shape", "returning_old_new_aliases", "pg18_compatibility"),
            bindings,
        )


class StatementFactorCycleMarkdownTest(unittest.TestCase):
    def setUp(self) -> None:
        self.snapshot = discover_statement_factor_cycle(ROOT)

    def test_inventory_markdown_contains_every_pending_factor_and_value(self) -> None:
        markdown = render_factor_inventory_markdown(self.snapshot)

        self.assertIn("剩余语句：177", markdown)
        self.assertIn("语句-因子：3,277", markdown)
        self.assertIn("因子值：9,676", markdown)
        self.assertEqual(177, markdown.count("<!-- statement:"))
        self.assertEqual(3277, markdown.count("<!-- factor:"))
        expected_row_ids = {
            row_id
            for entry in self.snapshot.pending_entries
            for factor in entry.factors
            for row_id in factor.row_ids
        }
        actual_row_ids = set(re.findall(r"<!-- row:(sfv-[0-9a-f]{24}) -->", markdown))
        self.assertEqual(9676, markdown.count("<!-- row:"))
        self.assertEqual(expected_row_ids, actual_row_ids)
        for entry in self.snapshot.pending_entries:
            self.assertIn(f"<!-- statement:{entry.statement_key} -->", markdown)
            self.assertIn(entry.matrix_path.as_posix(), markdown)
            for factor in entry.factors:
                self.assertIn(
                    f"<!-- factor:{entry.statement_key}:{factor.name} -->",
                    markdown,
                )
                for value in factor.values:
                    self.assertIn(
                        f"`{factor.name}={value}`",
                        markdown,
                    )

    def test_initial_plan_marks_only_cursor_and_dcl_as_retained(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_path = Path(temporary) / "progress.json"
            state = initialize_cycle_state(self.snapshot, state_path)
            markdown = render_cycle_plan_markdown(self.snapshot, state)

        self.assertEqual(6, markdown.count("[x]"))
        self.assertEqual(177, markdown.count("[ ]"))
        self.assertIn("下一条：`abort`", markdown)
        self.assertIn("cursor-factor-full-v1", markdown)
        self.assertIn("dcl-factor-full-v1", markdown)


class StatementFactorCycleProgressTest(unittest.TestCase):
    def setUp(self) -> None:
        self.snapshot = discover_statement_factor_cycle(ROOT)

    def write_bound_evidence(
        self,
        root: Path,
        *,
        statement_key: str = "abort",
        passed: bool = True,
    ) -> tuple[Path, Path]:
        package = root / "package"
        package.mkdir(parents=True)
        sql_path = package / "ABORT00001.sql"
        sql_path.write_text("ABORT;\n", encoding="utf-8")
        package_evidence = root / "package.json"
        package_evidence.write_text('{"kind":"test-package"}\n', encoding="utf-8")
        entry = next(
            item for item in self.snapshot.entries if item.statement_key == "abort"
        )
        evidence = root / "validation.json"
        evidence.write_text(
            json.dumps(
                {
                    "statement_key": statement_key,
                    "cycle_fingerprint": self.snapshot.fingerprint,
                    "passed": passed,
                    "issues": [],
                    "sql_file_count": 1,
                    "factor_value_count": entry.factor_value_count,
                    "sql_sha256": {
                        sql_path.name: hashlib.sha256(sql_path.read_bytes()).hexdigest()
                    },
                    "input_sha256": {
                        "matrix": entry.matrix_sha256,
                        "reference": entry.reference_sha256,
                        "applicability_universe_semantic": (
                            self.snapshot.universe_semantic_sha256
                        ),
                    },
                    "package_sha256": hashlib.sha256(
                        package_evidence.read_bytes()
                    ).hexdigest(),
                    "runtime_status": "not_run_static_sql_only",
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
        return package, evidence

    def test_completion_is_strictly_sequential_and_records_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state_path = root / "progress.json"
            package_path, evidence_path = self.write_bound_evidence(root / "bound")
            initialize_cycle_state(self.snapshot, state_path)

            with self.assertRaisesRegex(
                StatementFactorCycleError,
                "next pending statement is abort",
            ):
                complete_cycle_statement(
                    self.snapshot,
                    state_path,
                    "alter_aggregate",
                    package_path=package_path.as_posix(),
                    sql_file_count=1,
                    validation_evidence=evidence_path,
                )

            state = complete_cycle_statement(
                self.snapshot,
                state_path,
                "abort",
                package_path=package_path.as_posix(),
                sql_file_count=1,
                validation_evidence=evidence_path,
            )
            document = json.loads(state_path.read_text(encoding="utf-8"))

        self.assertEqual("completed", document["statements"]["abort"]["status"])
        self.assertEqual(1, document["statements"]["abort"]["sql_file_count"])
        self.assertEqual(
            "alter_aggregate",
            state.next_pending_statement,
        )
        markdown = render_cycle_plan_markdown(self.snapshot, state)
        abort_row = next(line for line in markdown.splitlines() if "`abort`" in line)
        self.assertIn("[x]", abort_row)
        self.assertIn("1", abort_row)
        self.assertIn("下一条：`alter_aggregate`", markdown)

    def test_initialization_refuses_to_overwrite_existing_progress(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            state_path = Path(temporary) / "progress.json"
            initialize_cycle_state(self.snapshot, state_path)
            before = state_path.read_bytes()

            with self.assertRaisesRegex(
                StatementFactorCycleError,
                "cycle state already exists",
            ):
                initialize_cycle_state(self.snapshot, state_path)

            self.assertEqual(before, state_path.read_bytes())

    def test_completion_rejects_missing_or_failed_validation_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state_path = root / "progress.json"
            initialize_cycle_state(self.snapshot, state_path)

            with self.assertRaisesRegex(
                StatementFactorCycleError,
                "validation evidence is missing",
            ):
                complete_cycle_statement(
                    self.snapshot,
                    state_path,
                    "abort",
                    package_path="artifacts/regress/by-factor/tcl/transaction/abort",
                    sql_file_count=1,
                    validation_evidence=root / "missing.json",
                )

            failed = root / "failed.json"
            failed.write_text('{"passed": false}\n', encoding="utf-8")
            with self.assertRaisesRegex(
                StatementFactorCycleError,
                "validation evidence did not pass",
            ):
                complete_cycle_statement(
                    self.snapshot,
                    state_path,
                    "abort",
                    package_path="artifacts/regress/by-factor/tcl/transaction/abort",
                    sql_file_count=1,
                    validation_evidence=failed,
                )

    def test_materialized_plan_is_refreshed_only_after_validated_completion(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state_path = root / "progress.json"
            inventory_path = root / "factors.md"
            plan_path = root / "plan.md"
            materialize_cycle_documents(
                self.snapshot,
                state_path=state_path,
                inventory_path=inventory_path,
                plan_path=plan_path,
            )
            before = plan_path.read_text(encoding="utf-8")
            self.assertIn("下一条：`abort`", before)
            self.assertTrue(inventory_path.is_file())

            package_path, evidence_path = self.write_bound_evidence(root / "bound")
            complete_cycle_statement(
                self.snapshot,
                state_path,
                "abort",
                package_path=package_path.as_posix(),
                sql_file_count=1,
                validation_evidence=evidence_path,
                plan_path=plan_path,
            )
            after = plan_path.read_text(encoding="utf-8")

        self.assertNotEqual(before, after)
        self.assertIn("下一条：`alter_aggregate`", after)
        abort_row = next(line for line in after.splitlines() if "`abort`" in line)
        self.assertIn("[x]", abort_row)

    def test_completion_binds_statement_inputs_and_real_sql_hashes(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state_path = root / "progress.json"
            initialize_cycle_state(self.snapshot, state_path)
            package, evidence = self.write_bound_evidence(
                root / "wrong",
                statement_key="alter_aggregate",
            )

            with self.assertRaisesRegex(
                StatementFactorCycleError,
                "validation evidence statement does not match abort",
            ):
                complete_cycle_statement(
                    self.snapshot,
                    state_path,
                    "abort",
                    package_path=package.as_posix(),
                    sql_file_count=1,
                    validation_evidence=evidence,
                )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            state_path = root / "progress.json"
            initialize_cycle_state(self.snapshot, state_path)
            package, evidence = self.write_bound_evidence(root / "tampered")
            (package / "ABORT00001.sql").write_text(
                "ABORT WORK;\n", encoding="utf-8"
            )

            with self.assertRaisesRegex(
                StatementFactorCycleError,
                "SQL SHA-256 map does not match",
            ):
                complete_cycle_statement(
                    self.snapshot,
                    state_path,
                    "abort",
                    package_path=package.as_posix(),
                    sql_file_count=1,
                    validation_evidence=evidence,
                )


if __name__ == "__main__":
    unittest.main()
