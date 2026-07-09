from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

import yaml


PROMOTION_TYPES = {
    "unexpected_failure": "bug_reproduction_candidate",
    "unexpected_success": "negative_oracle_review_candidate",
    "sqlstate_mismatch": "failure_oracle_review_candidate",
    "result_mismatch": "semantic_bug_candidate",
    "plan_mismatch": "plan_derived_extension_candidate",
    "cleanup_failure": "cleanup_hardening_candidate",
    "unclassified_failure": "manual_triage_candidate",
}


def load_yaml(path: Path) -> dict[str, Any]:
    parsed = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(parsed, dict):
        raise ValueError(f"{path}: diagnosis must be a mapping")
    return parsed


def build_promotion_candidates(diagnosis: dict[str, Any]) -> dict[str, Any]:
    feature = dict(diagnosis.get("feature") or {})
    candidates = []
    for cluster in list(diagnosis.get("clusters") or []):
        if not isinstance(cluster, dict):
            continue
        category = str(cluster.get("category") or "unclassified_failure")
        promotion_type = PROMOTION_TYPES.get(category, "manual_triage_candidate")
        for case in list(cluster.get("cases") or []):
            if not isinstance(case, dict):
                continue
            candidates.append(
                {
                    "id": f"{category}__{case.get('case_id')}",
                    "promotion_type": promotion_type,
                    "feature_key": str(feature.get("key") or "unknown_feature"),
                    "case_id": str(case.get("case_id") or ""),
                    "source_category": category,
                    "source_reason": str(cluster.get("reason") or ""),
                    "sql_path": str(case.get("sql_path") or ""),
                    "derived_extension": True,
                    "requires_human_review": True,
                    "counts_toward_required_baseline": False,
                    "recommended_action": _recommended_action(category),
                }
            )
    return {
        "schema_version": 1,
        "kind": "feedback_promotion_candidates",
        "feature": {"key": str(feature.get("key") or "unknown_feature")},
        "candidates": candidates,
    }


def _recommended_action(category: str) -> str:
    if category in {"unexpected_failure", "result_mismatch"}:
        return "minimize and review as possible product bug"
    if category == "plan_mismatch":
        return "review as derived plan-observation extension; do not replace result oracle"
    if category == "cleanup_failure":
        return "harden cleanup before promoting the case"
    if category in {"unexpected_success", "sqlstate_mismatch"}:
        return "review expected failure oracle and SQLSTATE attribution"
    return "manual triage required"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build human-reviewed promotion candidates from failure diagnosis.")
    parser.add_argument("--diagnosis", required=True, type=Path, help="failure_diagnosis_report yaml path")
    parser.add_argument("--output", type=Path, help="promotion candidates yaml output path")
    args = parser.parse_args(argv)

    try:
        promotion = build_promotion_candidates(load_yaml(args.diagnosis))
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}")
        return 1

    output = yaml.safe_dump(promotion, sort_keys=False, allow_unicode=True)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(output, encoding="utf-8")
    else:
        print(output, end="")
    print(f"PASS feedback promotion: candidates={len(promotion['candidates'])}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
