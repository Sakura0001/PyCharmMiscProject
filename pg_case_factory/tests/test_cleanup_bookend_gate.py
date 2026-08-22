"""TDD red tests for the hardened bookend gate.

``audit_cleanup_bookends`` locates the pre-cleanup and cleanup regions by the
bracket markers emitted by the shared ``cleanup_bookend`` helper, then enforces
the two HARD determinism rules that fix the 53.93% failure mass:

  * every DROP (table or otherwise) carries ``IF EXISTS`` (idempotent cleanup);
  * ``DROP OWNED BY`` is forbidden in pre-cleanup (the role may not exist yet on
    a fresh database, which crashes the run before the target statement).

Reverse table-creation order is intentionally left as a WARNING in
``audit_complete_table_script`` (not elevated to an issue): the helper always
emits ``CASCADE`` so order is semantically moot, and elevating would newly fail
same-order scripts and break the Phase-0 "0 new failures" exit criterion.
"""

from __future__ import annotations

import unittest

from pg_case_factory import regression_style
from pg_case_factory.regression_style import (
    CLEANUP_BOOKEND_GATE_MODE,
    CleanupBookendAuditReport,
    RegressionStyleError,
    audit_cleanup_bookends,
    enforce_cleanup_bookends,
)

# A fully conformant script: pre-cleanup has IF EXISTS + no DROP OWNED BY;
# cleanup has DROP OWNED BY (allowed, post-target) then DROP ROLE then tables.
GOOD_SCRIPT = """\
-- cleanup-bookend: pre-cleanup-begin
DROP TABLE IF EXISTS t CASCADE;
DROP ROLE IF EXISTS r;
-- cleanup-bookend: pre-cleanup-end
SELECT 1 AS target;
-- cleanup-bookend: cleanup-begin
DROP OWNED BY r CASCADE;
DROP ROLE IF EXISTS r;
DROP TABLE IF EXISTS t CASCADE;
-- cleanup-bookend: cleanup-end
"""

# Pre-cleanup DROP without IF EXISTS -> bare drop crash on fresh DB.
BAD_PRE_BARE_DROP = """\
-- cleanup-bookend: pre-cleanup-begin
DROP AGGREGATE foo(int);
-- cleanup-bookend: pre-cleanup-end
SELECT 1 AS target;
-- cleanup-bookend: cleanup-begin
DROP AGGREGATE IF EXISTS foo(int) CASCADE;
-- cleanup-bookend: cleanup-end
"""

# Pre-cleanup DROP OWNED BY -> role may not exist on fresh DB -> crash.
BAD_PRE_DROP_OWNED = """\
-- cleanup-bookend: pre-cleanup-begin
DROP OWNED BY r CASCADE;
-- cleanup-bookend: pre-cleanup-end
SELECT 1 AS target;
-- cleanup-bookend: cleanup-begin
DROP OWNED BY r CASCADE;
DROP ROLE IF EXISTS r;
-- cleanup-bookend: cleanup-end
"""

# Cleanup DROP without IF EXISTS -> non-idempotent (run-02 crash).
BAD_CLEANUP_BARE_DROP = """\
-- cleanup-bookend: pre-cleanup-begin
DROP AGGREGATE IF EXISTS foo(int) CASCADE;
-- cleanup-bookend: pre-cleanup-end
SELECT 1 AS target;
-- cleanup-bookend: cleanup-begin
DROP AGGREGATE foo(int);
-- cleanup-bookend: cleanup-end
"""

# No markers -> unmigrated render (warn mode: warning; enforce: issue).
NO_MARKERS = """\
DROP TABLE IF EXISTS t CASCADE;
SELECT 1 AS target;
DROP TABLE IF EXISTS t CASCADE;
"""

# Malformed regions: begin with no matching end.
UNBALANCED_MARKERS = """\
-- cleanup-bookend: pre-cleanup-begin
DROP TABLE IF EXISTS t CASCADE;
SELECT 1 AS target;
-- cleanup-bookend: cleanup-begin
DROP TABLE IF EXISTS t CASCADE;
-- cleanup-bookend: cleanup-end
"""


class TestAuditCleanupBookends(unittest.TestCase):
    def test_good_script_passes(self) -> None:
        report = audit_cleanup_bookends(GOOD_SCRIPT)
        self.assertIsInstance(report, CleanupBookendAuditReport)
        self.assertTrue(report.passed, msg=f"issues={report.issues}")
        self.assertEqual(report.issues, ())

    def test_pre_cleanup_bare_drop_is_issue(self) -> None:
        report = audit_cleanup_bookends(BAD_PRE_BARE_DROP)
        self.assertFalse(report.passed)
        self.assertTrue(
            any("IF EXISTS" in i for i in report.issues), msg=f"issues={report.issues}"
        )

    def test_pre_cleanup_drop_owned_by_is_issue(self) -> None:
        report = audit_cleanup_bookends(BAD_PRE_DROP_OWNED)
        self.assertFalse(report.passed)
        self.assertTrue(
            any("DROP OWNED BY" in i for i in report.issues), msg=f"issues={report.issues}"
        )

    def test_cleanup_bare_drop_is_issue(self) -> None:
        report = audit_cleanup_bookends(BAD_CLEANUP_BARE_DROP)
        self.assertFalse(report.passed)
        self.assertTrue(
            any("IF EXISTS" in i for i in report.issues), msg=f"issues={report.issues}"
        )

    def test_drop_owned_by_allowed_in_cleanup_only(self) -> None:
        # GOOD_SCRIPT has DROP OWNED BY in cleanup -> no issue for it.
        report = audit_cleanup_bookends(GOOD_SCRIPT)
        for issue in report.issues:
            self.assertNotIn("DROP OWNED BY", issue)
        # And the cleanup region must list the DROP OWNED BY statement.
        self.assertTrue(
            any("DROP OWNED BY" in s for s in report.cleanup_statements),
            msg=f"cleanup_statements={report.cleanup_statements}",
        )

    def test_no_markers_warn_mode_is_warning_not_issue(self) -> None:
        report = audit_cleanup_bookends(NO_MARKERS)
        self.assertTrue(report.passed, msg=f"issues={report.issues}")
        self.assertTrue(
            any("marker" in w.lower() for w in report.warnings),
            msg=f"warnings={report.warnings}",
        )

    def test_no_markers_strict_is_issue(self) -> None:
        report = audit_cleanup_bookends(NO_MARKERS, strict_markers=True)
        self.assertFalse(report.passed)
        self.assertTrue(
            any("marker" in i.lower() for i in report.issues), msg=f"issues={report.issues}"
        )

    def test_unbalanced_markers_warns(self) -> None:
        report = audit_cleanup_bookends(UNBALANCED_MARKERS)
        self.assertTrue(
            any("marker" in w.lower() or "unbalanced" in w.lower() for w in report.warnings)
            or not report.passed,
            msg=f"warnings={report.warnings} issues={report.issues}",
        )

    def test_empty_sql_rejected(self) -> None:
        with self.assertRaises(RegressionStyleError):
            audit_cleanup_bookends("")

    def test_non_string_rejected(self) -> None:
        with self.assertRaises(RegressionStyleError):
            audit_cleanup_bookends(None)  # type: ignore[arg-type]

    def test_pre_cleanup_region_isolated_from_cleanup(self) -> None:
        # A bare drop in cleanup must not be reported as a pre-cleanup issue.
        report = audit_cleanup_bookends(BAD_CLEANUP_BARE_DROP)
        pre_text = " ".join(report.pre_cleanup_statements)
        self.assertIn("IF EXISTS", pre_text)


class TestEnforceCleanupBookends(unittest.TestCase):
    def setUp(self) -> None:
        self._saved = regression_style.CLEANUP_BOOKEND_GATE_MODE

    def tearDown(self) -> None:
        regression_style.CLEANUP_BOOKEND_GATE_MODE = self._saved

    def test_warn_mode_returns_report_without_raising(self) -> None:
        regression_style.CLEANUP_BOOKEND_GATE_MODE = "warn"
        report = enforce_cleanup_bookends(BAD_PRE_BARE_DROP)
        self.assertFalse(report.passed)

    def test_enforce_mode_raises_on_pre_cleanup_bare_drop(self) -> None:
        regression_style.CLEANUP_BOOKEND_GATE_MODE = "enforce"
        with self.assertRaises(RegressionStyleError):
            enforce_cleanup_bookends(BAD_PRE_BARE_DROP)

    def test_enforce_mode_raises_on_pre_cleanup_drop_owned(self) -> None:
        regression_style.CLEANUP_BOOKEND_GATE_MODE = "enforce"
        with self.assertRaises(RegressionStyleError):
            enforce_cleanup_bookends(BAD_PRE_DROP_OWNED)

    def test_enforce_mode_passes_good_script(self) -> None:
        regression_style.CLEANUP_BOOKEND_GATE_MODE = "enforce"
        report = enforce_cleanup_bookends(GOOD_SCRIPT)
        self.assertTrue(report.passed)

    def test_enforce_mode_raises_on_unmigrated_no_markers(self) -> None:
        regression_style.CLEANUP_BOOKEND_GATE_MODE = "enforce"
        with self.assertRaises(RegressionStyleError):
            enforce_cleanup_bookends(NO_MARKERS)

    def test_default_mode_is_warn(self) -> None:
        self.assertEqual(CLEANUP_BOOKEND_GATE_MODE, "warn")


if __name__ == "__main__":
    unittest.main()
