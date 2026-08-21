from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest

from pg_case_factory.full_sql_runtime import (
    EVIDENCE_COMPATIBILITY,
    EVIDENCE_OBSERVATIONAL,
    EVIDENCE_STRICT,
    compile_runtime_manifest,
)


STRICT_SQL = """-- case_id: STRICT0001
-- expected_outcome: success
-- expected_sqlstate: 00000
-- primary-target-begin
SELECT true;
-- primary-target-end
\\echo PGCF_TARGET_SQLSTATE=:SQLSTATE
SELECT :'SQLSTATE' = '00000' AS target_sqlstate_matches_expected;
-- 5. cleanup
"""


class RuntimeManifestTest(unittest.TestCase):
    def test_manifest_uses_sql_files_not_schedules_and_deduplicates_retained(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            current = root / "artifacts/regress/by-factor/ddl/example"
            current.mkdir(parents=True)
            (current / "STRICT0001.sql").write_text(STRICT_SQL)
            (current / "STRICT0002.sql").write_text(
                STRICT_SQL.replace("STRICT0001", "STRICT0002")
            )
            (current / "serial_schedule").write_text("test: STRICT0001\n")
            (current / "external_schedule").write_text("test: STRICT0002\n")

            retained = root / "artifacts/regress/cursor-factor-full-v1/sql"
            retained.mkdir(parents=True)
            legacy = """-- case_id: CUR00001
-- description  : Verify PostgreSQL 18.4 CLOSE with factors
-- factor expected_status=failure
CLOSE missing_cursor;
"""
            (retained / "CUR00001.sql").write_text(legacy)

            progress_path = root / "progress.json"
            progress_path.write_text(
                json.dumps(
                    {
                        "statements": {
                            "example": {
                                "status": "completed",
                                "package_path": str(current.relative_to(root)),
                                "sql_file_count": 2,
                            },
                            "close": {
                                "status": "retained_existing",
                                "package_path": "artifacts/regress/cursor-factor-full-v1",
                            },
                            "declare": {
                                "status": "retained_existing",
                                "package_path": "artifacts/regress/cursor-factor-full-v1",
                            },
                        }
                    }
                )
            )

            manifest = compile_runtime_manifest(root, progress_path)

        self.assertEqual(3, len(manifest))
        by_id = {case.case_id: case for case in manifest}
        self.assertEqual(EVIDENCE_STRICT, by_id["STRICT0001"].evidence_level)
        self.assertFalse(by_id["STRICT0001"].external)
        self.assertTrue(by_id["STRICT0002"].external)
        self.assertEqual(EVIDENCE_OBSERVATIONAL, by_id["CUR00001"].evidence_level)
        self.assertEqual("close", by_id["CUR00001"].statement_key)
        self.assertEqual("expected_failure", by_id["CUR00001"].expected_outcome)

    def test_compatibility_case_is_bound_to_plan_metadata_and_sql_sha(self) -> None:
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            package = root / "artifacts/regress/by-factor/ddl/legacy"
            package.mkdir(parents=True)
            sql = """-- case_id: LEGACY0001
-- factor expected_status=failure
SELECT false AS target_sqlstate_matches;
"""
            sql_path = package / "LEGACY0001.sql"
            sql_path.write_text(sql)
            evidence = (
                root
                / "artifacts/intermediates/remaining-statement-factor-cycle/legacy"
            )
            evidence.mkdir(parents=True)
            (evidence / "plan.json").write_text(
                json.dumps(
                    {
                        "cases": [
                            {
                                "case_id": "LEGACY0001",
                                "sql_filename": "LEGACY0001.sql",
                                "object_prefix": "legacy_0001_",
                                "outcome": "expected_failure",
                                "derived_axes": {"expected_sqlstate": "42704"},
                            }
                        ]
                    }
                )
            )
            progress_path = root / "progress.json"
            progress_path.write_text(
                json.dumps(
                    {
                        "statements": {
                            "legacy": {
                                "status": "completed",
                                "package_path": str(package.relative_to(root)),
                                "sql_file_count": 1,
                            }
                        }
                    }
                )
            )

            [case] = compile_runtime_manifest(root, progress_path)

        self.assertEqual(EVIDENCE_COMPATIBILITY, case.evidence_level)
        self.assertEqual("expected_failure", case.expected_outcome)
        self.assertEqual("42704", case.expected_sqlstate)
        self.assertEqual(hashlib.sha256(sql.encode()).hexdigest(), case.sql_sha256)
        self.assertEqual("legacy_0001_", case.object_prefix)


if __name__ == "__main__":
    unittest.main()
