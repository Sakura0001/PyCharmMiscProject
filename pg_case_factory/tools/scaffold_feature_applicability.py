from __future__ import annotations

import argparse
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = PROJECT_ROOT / "src"
if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))

from pg_case_factory.applicability import (  # noqa: E402
    ApplicabilityValidationError,
    DEFAULT_LEDGER_PATH,
    SHIPPED_UNIVERSE_COUNTS,
    compile_feature_applicability_plan,
    load_feature_applicability_index,
    load_shipped_applicability_universe,
    refresh_feature_applicability_index,
    scaffold_feature_applicability,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Scaffold or refresh PostgreSQL 18.4 feature applicability reviews."
    )
    commands = parser.add_subparsers(dest="command", required=True)

    scaffold = commands.add_parser(
        "scaffold",
        help="create 183 pending statement review files",
    )
    scaffold.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="pg_case_factory repository root",
    )
    scaffold.add_argument(
        "--feature-id",
        required=True,
        help="stable feature identifier used by every review",
    )
    scaffold.add_argument(
        "--output",
        required=True,
        type=Path,
        help="new output directory for the index and 183 review files",
    )

    refresh = commands.add_parser(
        "refresh",
        help="refresh review SHA values without changing review decisions",
    )
    refresh.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="pg_case_factory repository root",
    )
    refresh.add_argument(
        "--index",
        required=True,
        type=Path,
        help="existing feature_applicability_index.yaml",
    )
    validate = commands.add_parser(
        "validate",
        help="strictly validate index, reviews, locators, witnesses, and completeness",
    )
    validate.add_argument(
        "--root",
        type=Path,
        default=Path.cwd(),
        help="pg_case_factory repository root",
    )
    validate.add_argument(
        "--index",
        required=True,
        type=Path,
        help="existing feature_applicability_index.yaml",
    )
    validate.add_argument(
        "--requirement-id",
        action="append",
        default=None,
        help="known feature requirement ID; repeat for every manifest requirement",
    )
    validate.add_argument(
        "--require-complete",
        action="store_true",
        help="reject pending statement, factor, or value decisions",
    )
    validate.add_argument(
        "--draft",
        action="store_true",
        help="allow covered rows to omit compiler-generated obligation bindings",
    )
    compile_command = commands.add_parser(
        "compile",
        help="compile covered draft rows into a separate plan and backfill bindings",
    )
    compile_command.add_argument("--root", type=Path, default=Path.cwd())
    compile_command.add_argument("--manifest", type=Path, required=True)
    compile_command.add_argument("--base-plan", type=Path, required=True)
    compile_command.add_argument("--index", type=Path, required=True)
    compile_command.add_argument("--output", type=Path, required=True)
    compile_command.add_argument("--source-root", type=Path, default=None)
    compile_command.add_argument("--inventory-root", type=Path, default=None)
    arguments = parser.parse_args(argv)

    root = arguments.root.resolve()
    if arguments.command == "compile":
        try:
            result = compile_feature_applicability_plan(
                manifest_path=arguments.manifest,
                base_plan_path=arguments.base_plan,
                index_path=arguments.index,
                output_path=arguments.output,
                repository_root=root,
                source_root=arguments.source_root,
                inventory_root=arguments.inventory_root or root,
                expected_counts=SHIPPED_UNIVERSE_COUNTS,
            )
        except (ApplicabilityValidationError, OSError, ValueError) as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        summary = result.applicability.summary
        print(
            "PASS feature applicability compilation: "
            f"output={result.output_path} covered={summary.covered} "
            f"pending={summary.pending} generated_axes={len(result.generated_axis_ids)} "
            f"generated_test_points={len(result.generated_test_point_ids)} "
            f"canonical_upper_bound={result.canonical_upper_bound}"
        )
        return 0

    if arguments.command == "validate":
        try:
            loaded = load_feature_applicability_index(
                arguments.index,
                repository_root=root,
                known_requirement_ids=arguments.requirement_id,
                require_complete=arguments.require_complete,
                expected_counts=SHIPPED_UNIVERSE_COUNTS,
                draft=arguments.draft,
            )
        except ApplicabilityValidationError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        summary = loaded.summary
        print(
            "PASS feature applicability validation: "
            f"statements={loaded.universe.counts.statements} "
            f"factor_pairs={loaded.universe.counts.statement_factor_pairs} "
            f"value_rows={summary.total} covered={summary.covered} "
            f"justified_exclusion={summary.justified_exclusion} "
            f"pending={summary.pending} unbound_covered={summary.unbound_covered} "
            f"complete={str(summary.complete).lower()}"
        )
        return 0

    if arguments.command == "refresh":
        try:
            index_path = refresh_feature_applicability_index(
                arguments.index,
                repository_root=root,
                expected_counts=SHIPPED_UNIVERSE_COUNTS,
            )
        except ApplicabilityValidationError as exc:
            print(f"ERROR: {exc}", file=sys.stderr)
            return 1
        print(
            "PASS feature applicability index refresh: "
            f"index={index_path}; run semantic validation next"
        )
        return 0

    ledger_relative = DEFAULT_LEDGER_PATH.as_posix()

    try:
        universe = load_shipped_applicability_universe(root)
        index_path = scaffold_feature_applicability(
            universe,
            arguments.output,
            feature_id=arguments.feature_id,
            universe_path=ledger_relative,
        )
        loaded = load_feature_applicability_index(
            index_path,
            repository_root=root,
            require_complete=False,
            expected_counts=SHIPPED_UNIVERSE_COUNTS,
        )
    except ApplicabilityValidationError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    summary = loaded.summary
    print(
        "PASS feature applicability scaffold: "
        f"index={index_path.resolve()} "
        f"statements={loaded.universe.counts.statements} "
        f"factor_pairs={loaded.universe.counts.statement_factor_pairs} "
        f"value_rows={summary.total} pending={summary.pending}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
