from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "pg-sql-generation"


def _read(relative_path: str) -> str:
    return (SKILL_ROOT / relative_path).read_text(encoding="utf-8")


def test_feature_test_loop_references_exist_and_define_contracts():
    required = {
        "references/common/execution_loop_policy.md": [
            "feature_execution_report",
            "run_generated_sql.py",
            "audit_execution_report.py",
            "cases",
        ],
        "references/common/query_oracle_policy.md": [
            "query_result_oracle",
            "EXPLAIN",
            "row_order",
            "plan_observation",
        ],
        "references/common/failure_diagnosis_policy.md": [
            "failure_diagnosis_report",
            "unexpected_failure",
            "sqlstate_mismatch",
            "plan_mismatch",
        ],
        "references/common/feedback_promotion_policy.md": [
            "feedback_promotion_candidates",
            "derived_extension",
            "requires_human_review",
            "counts_toward_required_baseline",
        ],
        "references/mainflow/run_feature_test_loop.md": [
            "run_generated_sql.py",
            "audit_execution_report.py",
            "diagnose_execution_failures.py",
            "promote_execution_feedback.py",
        ],
        "references/templates/feature_test_intake_template.md": [
            "feature_key",
            "statement_scope",
            "query_context",
            "loop_budget",
        ],
    }

    for relative_path, expected_terms in required.items():
        text = _read(relative_path)
        for term in expected_terms:
            assert term in text, f"{relative_path} missing {term}"


def test_skill_navigation_exposes_feature_test_loop():
    skill_text = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")

    assert "references/mainflow/run_feature_test_loop.md" in skill_text
    assert "references/common/execution_loop_policy.md" in skill_text
    assert "references/common/query_oracle_policy.md" in skill_text
    assert "references/common/failure_diagnosis_policy.md" in skill_text
    assert "references/common/feedback_promotion_policy.md" in skill_text


def test_generate_sql_mainflow_routes_loop_capable_requests():
    text = _read("references/mainflow/generate_sql_from_request.md")

    assert "references/mainflow/run_feature_test_loop.md" in text
    assert "references/common/execution_loop_policy.md" in text
    assert "references/templates/feature_test_intake_template.md" in text
