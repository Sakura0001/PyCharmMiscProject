"""PostgreSQL 18 ALTER AGGREGATE full regress design and renderer.

The shipped matrix declares 52 canonical factor values, but its five nominal
``exhaustive`` axes are not independent.  This module resolves the legal
signature/form, branch/state, and state/status bindings explicitly, then adds
the PostgreSQL 18 grammar and privilege boundaries that are absent from the
canonical ledger.  Every logical cell is emitted as one self-contained SQL
file so an expected failure always has one primary cause.
"""

from __future__ import annotations

import itertools
from dataclasses import dataclass
from typing import Callable, Mapping

from .remaining_statement_regress import (
    FactorValueDecision,
    RemainingStatementRegressError,
    StatementRegressCase,
    StatementRegressPlan,
    _header,
)
from .statement_factor_cycle import (
    StatementCycleEntry,
    StatementFactorCycleSnapshot,
)


@dataclass(frozen=True)
class AggregateSignatureSpec:
    signature_id: str
    canonical_signature: str
    aggregate_form: str
    fixture_kind: str
    target_signature: str
    create_signature: str
    aggregate_kind: str
    direct_arg_count: int
    flat_arg_count: int


_SIGNATURES = (
    AggregateSignatureSpec(
        "s01_star_zero_arg", "star_zero_arg", "zero_arg", "zero", "*", "*", "n", 0, 0
    ),
    AggregateSignatureSpec(
        "s02_single_arg", "single_argtype", "single_arg", "single", "integer", "original_value integer", "n", 0, 1
    ),
    AggregateSignatureSpec(
        "s03_multi_arg", "multi_argtype", "multi_arg", "multi", "integer, text", "original_value integer, original_note text", "n", 0, 2
    ),
    AggregateSignatureSpec(
        "s04_ordered_set", "ordered_set_signature", "ordered_set", "ordered", "double precision ORDER BY integer", "direct_value double precision ORDER BY ordered_value integer", "o", 1, 2
    ),
    AggregateSignatureSpec(
        "s05_abbreviated_ordered_set", "abbreviated_ordered_set", "ordered_set", "ordered", "double precision, integer", "direct_value double precision ORDER BY ordered_value integer", "o", 1, 2
    ),
    AggregateSignatureSpec(
        "s06_ordered_no_direct", "ordered_set_signature", "ordered_set", "ordered_no_direct", "ORDER BY integer", "ORDER BY ordered_value integer", "o", 0, 1
    ),
    AggregateSignatureSpec(
        "s07_named_arg", "single_argtype", "single_arg", "single", "ignored_name integer", "original_name integer", "n", 0, 1
    ),
    AggregateSignatureSpec(
        "s08_in_arg", "single_argtype", "single_arg", "single", "IN integer", "original_name integer", "n", 0, 1
    ),
    AggregateSignatureSpec(
        "s09_in_named_arg", "single_argtype", "single_arg", "single", "IN ignored_name integer", "original_name integer", "n", 0, 1
    ),
    AggregateSignatureSpec(
        "s10_variadic", "single_argtype", "single_arg", "variadic", "VARIADIC integer[]", "VARIADIC original_values integer[]", "n", 0, 1
    ),
    AggregateSignatureSpec(
        "s11_variadic_named", "single_argtype", "single_arg", "variadic", "VARIADIC ignored_values integer[]", "VARIADIC original_values integer[]", "n", 0, 1
    ),
    AggregateSignatureSpec(
        "s12_ordered_variadic", "ordered_set_signature", "ordered_set", "ordered_variadic", 'VARIADIC "any" ORDER BY VARIADIC "any"', 'VARIADIC "any" ORDER BY VARIADIC "any"', "h", 1, 1
    ),
    AggregateSignatureSpec(
        "s13_ordered_variadic_abbreviated", "abbreviated_ordered_set", "ordered_set", "ordered_variadic", 'VARIADIC "any"', 'VARIADIC "any" ORDER BY VARIADIC "any"', "h", 1, 1
    ),
    AggregateSignatureSpec(
        "s14_hypothetical_set", "ordered_set_signature", "ordered_set", "hypothetical", "integer ORDER BY integer", "direct_value integer ORDER BY ordered_value integer", "h", 1, 2
    ),
)
_SIGNATURE_BY_ID = {item.signature_id: item for item in _SIGNATURES}
_CANONICAL_SIGNATURES = _SIGNATURES[:5]

_NAME_SHAPES = ("plain_identifier", "quoted_identifier", "schema_qualified")
_NEW_NAME_SHAPES = ("plain_identifier", "quoted_identifier", "reserved_word")
_OWNER_SHAPES = ("CURRENT_ROLE", "CURRENT_USER", "SESSION_USER", "plain_role")
_BRANCHES = ("rename", "owner", "set_schema")


def _factor_tokens(*values: str | None) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def _signature_tokens(spec: AggregateSignatureSpec) -> tuple[str, ...]:
    return (
        f"aggregate_signature={spec.canonical_signature}",
        f"aggregate_form={spec.aggregate_form}",
    )


def _branch_token(branch: str) -> str:
    return {
        "rename": "statement_branch=branch_rename",
        "owner": "statement_branch=branch_owner",
        "set_schema": "statement_branch=branch_set_schema",
    }[branch]


def _available_state_token(branch: str) -> str:
    return {
        "rename": "target_state=new_name_available",
        "owner": "target_state=new_owner_available",
        "set_schema": "target_state=new_schema_available",
    }[branch]


def _case(
    ordinal: int,
    *,
    group: str,
    case_type: str,
    outcome: str,
    axes: Mapping[str, str],
    factor_values: tuple[str, ...],
    strategy: str,
    description: str,
    expected_anchor: str,
    execution_profile: str = "same_session_multiphase",
) -> StatementRegressCase:
    number = f"{ordinal:05d}"
    return StatementRegressCase(
        ordinal=ordinal,
        case_id=f"ALTERAGGREGATE{number}",
        sql_filename=f"ALTERAGGREGATE{number}.sql",
        object_prefix=f"alteraggregate_{number}_",
        case_group=group,
        case_type=case_type,
        outcome=outcome,
        execution_profile=execution_profile,
        derived_axes=dict(axes),
        factor_values=factor_values,
        combination_strategy=strategy,
        description=description,
        expected_anchor=expected_anchor,
    )


def _spec_axes(spec: AggregateSignatureSpec) -> dict[str, str]:
    return {
        "signature_id": spec.signature_id,
        "signature_key": spec.canonical_signature,
        "fixture_kind": spec.fixture_kind,
        "target_signature": spec.target_signature,
        "aggregate_kind": spec.aggregate_kind,
        "direct_arg_count": str(spec.direct_arg_count),
        "flat_arg_count": str(spec.flat_arg_count),
    }


def _rotate(values: tuple[str, ...], ordinal: int) -> str:
    return values[(ordinal - 1) % len(values)]


def _build_cases() -> tuple[StatementRegressCase, ...]:
    cases: list[StatementRegressCase] = []

    def add(**kwargs: object) -> None:
        cases.append(_case(len(cases) + 1, **kwargs))  # type: ignore[arg-type]

    # 336 success cells.  These are conditional products: signature and form
    # are one bound object, while branch-specific target syntaxes are crossed
    # only with the lexical shapes applicable to that branch.
    for spec, name_shape, new_name_shape in itertools.product(
        _SIGNATURES, _NAME_SHAPES, _NEW_NAME_SHAPES
    ):
        ordinal = len(cases) + 1
        cleanup = _rotate(
            ("DROP_AGGREGATE", "DROP_AGGREGATE_IF_EXISTS", "DROP_AGGREGATE_CASCADE"),
            ordinal,
        )
        verification = _rotate(
            ("pg_aggregate_actual_execution", "pg_aggregate_catalog_query", "pg_proc_query"),
            ordinal,
        )
        add(
            group="success_rename_product",
            case_type="syntax_semantics",
            outcome="success",
            axes={
                **_spec_axes(spec),
                "branch": "rename",
                "aggregate_name_shape": name_shape,
                "new_name_shape": new_name_shape,
                "cleanup_mode": cleanup,
                "verification_mode": verification,
                "expected_sqlstate": "00000",
            },
            factor_values=_factor_tokens(
                _branch_token("rename"),
                *_signature_tokens(spec),
                "expected_status=success",
                _available_state_token("rename"),
                f"aggregate_name_shape={name_shape}",
                f"new_name_shape={new_name_shape}",
                "privilege_level=superuser",
                f"verification_mode={verification}",
                f"cleanup_mode={cleanup}",
            ),
            strategy="full conditional Cartesian S14 signatures × 3 aggregate-name shapes × 3 rename-target shapes",
            description=f"Verify ALTER AGGREGATE RENAME for {spec.signature_id}, {name_shape}, {new_name_shape}",
            expected_anchor="SQLSTATE 00000, stable aggregate identity, new name only, and unchanged execution result",
        )

    for spec, name_shape, owner_shape in itertools.product(
        _SIGNATURES, _NAME_SHAPES, _OWNER_SHAPES
    ):
        ordinal = len(cases) + 1
        cleanup = _rotate(
            ("DROP_AGGREGATE", "DROP_AGGREGATE_IF_EXISTS", "DROP_AGGREGATE_CASCADE"),
            ordinal,
        )
        verification = _rotate(
            ("pg_aggregate_actual_execution", "pg_aggregate_catalog_query", "pg_proc_query"),
            ordinal,
        )
        add(
            group="success_owner_product",
            case_type="syntax_semantics",
            outcome="success",
            axes={
                **_spec_axes(spec),
                "branch": "owner",
                "aggregate_name_shape": name_shape,
                "owner_shape": owner_shape,
                "cleanup_mode": cleanup,
                "verification_mode": verification,
                "expected_sqlstate": "00000",
            },
            factor_values=_factor_tokens(
                _branch_token("owner"),
                *_signature_tokens(spec),
                "expected_status=success",
                _available_state_token("owner"),
                f"aggregate_name_shape={name_shape}",
                f"new_owner_shape={owner_shape}",
                "privilege_level=superuser",
                (
                    "owner_membership=member_of_new_owner"
                    if owner_shape == "plain_role"
                    else None
                ),
                f"verification_mode={verification}",
                f"cleanup_mode={cleanup}",
            ),
            strategy="full conditional Cartesian S14 signatures × 3 aggregate-name shapes × 4 OWNER RoleSpec forms",
            description=f"Verify ALTER AGGREGATE OWNER for {spec.signature_id}, {name_shape}, {owner_shape}",
            expected_anchor="SQLSTATE 00000, expected proowner, stable identity, and unchanged execution result",
        )

    for spec, name_shape in itertools.product(_SIGNATURES, _NAME_SHAPES):
        ordinal = len(cases) + 1
        cleanup = _rotate(
            ("DROP_AGGREGATE", "DROP_AGGREGATE_IF_EXISTS", "DROP_AGGREGATE_CASCADE"),
            ordinal,
        )
        verification = _rotate(
            ("pg_aggregate_actual_execution", "pg_aggregate_catalog_query", "pg_proc_query"),
            ordinal,
        )
        add(
            group="success_set_schema_product",
            case_type="syntax_semantics",
            outcome="success",
            axes={
                **_spec_axes(spec),
                "branch": "set_schema",
                "aggregate_name_shape": name_shape,
                "cleanup_mode": cleanup,
                "verification_mode": verification,
                "expected_sqlstate": "00000",
            },
            factor_values=_factor_tokens(
                _branch_token("set_schema"),
                *_signature_tokens(spec),
                "expected_status=success",
                _available_state_token("set_schema"),
                f"aggregate_name_shape={name_shape}",
                "new_schema_shape=existing_schema",
                "privilege_level=superuser",
                f"verification_mode={verification}",
                f"cleanup_mode={cleanup}",
            ),
            strategy="full conditional Cartesian S14 signatures × 3 aggregate-name shapes for SET SCHEMA",
            description=f"Verify ALTER AGGREGATE SET SCHEMA for {spec.signature_id}, {name_shape}",
            expected_anchor="SQLSTATE 00000, source absence, target identity, and unchanged execution result",
        )

    # 336 branch-state failure cells, again compatibility-filtered rather than
    # crossing unrelated target states or independent expected_status values.
    for spec, name_shape, new_name_shape in itertools.product(
        _SIGNATURES, _NAME_SHAPES, _NEW_NAME_SHAPES
    ):
        add(
            group="failure_rename_conflict_product",
            case_type="negative",
            outcome="expected_failure",
            axes={
                **_spec_axes(spec),
                "branch": "rename",
                "aggregate_name_shape": name_shape,
                "new_name_shape": new_name_shape,
                "expected_sqlstate": "42723",
                "failure_cause": "same_signature_aggregate_conflict",
            },
            factor_values=_factor_tokens(
                _branch_token("rename"),
                *_signature_tokens(spec),
                "expected_status=failure",
                "target_state=new_name_conflict",
                f"aggregate_name_shape={name_shape}",
                f"new_name_shape={new_name_shape}",
                "new_name_conflict=same_signature_conflict",
                "verification_mode=pg_aggregate_catalog_query",
                "cleanup_mode=DROP_AGGREGATE_CASCADE",
            ),
            strategy="full conditional Cartesian S14 signatures × 3 aggregate-name shapes × 3 conflicting rename-target shapes",
            description=f"Reject ALTER AGGREGATE RENAME conflict for {spec.signature_id}",
            expected_anchor="SQLSTATE 42723 and both original aggregate identities unchanged",
        )

    for spec, name_shape, unavailable_reason in itertools.product(
        _SIGNATURES,
        _NAME_SHAPES,
        ("nonexistent_role", "cannot_set_role", "new_owner_no_create"),
    ):
        sqlstate = "42704" if unavailable_reason == "nonexistent_role" else "42501"
        add(
            group="failure_owner_unavailable_product",
            case_type="negative",
            outcome="expected_failure",
            axes={
                **_spec_axes(spec),
                "branch": "owner",
                "aggregate_name_shape": name_shape,
                "owner_shape": "plain_role",
                "unavailable_reason": unavailable_reason,
                "expected_sqlstate": sqlstate,
            },
            factor_values=_factor_tokens(
                _branch_token("owner"),
                *_signature_tokens(spec),
                "expected_status=failure",
                "target_state=new_owner_unavailable",
                f"aggregate_name_shape={name_shape}",
                "new_owner_shape=plain_role",
                "privilege_level=aggregate_owner",
                (
                    "new_owner_not_exists=nonexistent_role"
                    if unavailable_reason == "nonexistent_role"
                    else None
                ),
                (
                    "owner_membership=not_member_of_new_owner"
                    if unavailable_reason == "cannot_set_role"
                    else None
                ),
                (
                    "insufficient_privilege=no_create_on_schema"
                    if unavailable_reason == "new_owner_no_create"
                    else None
                ),
                "verification_mode=pg_proc_query",
                "cleanup_mode=DROP_AGGREGATE_IF_EXISTS",
            ),
            strategy="full conditional Cartesian S14 signatures × 3 aggregate-name shapes × 3 isolated OWNER-unavailable reasons",
            description=f"Reject ALTER AGGREGATE OWNER for isolated {unavailable_reason}",
            expected_anchor=f"SQLSTATE {sqlstate} and original proowner unchanged",
        )

    for spec, name_shape, target_state in itertools.product(
        _SIGNATURES, _NAME_SHAPES, ("conflict", "nonexistent")
    ):
        sqlstate = "42723" if target_state == "conflict" else "3F000"
        add(
            group="failure_set_schema_state_product",
            case_type="negative",
            outcome="expected_failure",
            axes={
                **_spec_axes(spec),
                "branch": "set_schema",
                "aggregate_name_shape": name_shape,
                "target_state": target_state,
                "expected_sqlstate": sqlstate,
            },
            factor_values=_factor_tokens(
                _branch_token("set_schema"),
                *_signature_tokens(spec),
                "expected_status=failure",
                f"aggregate_name_shape={name_shape}",
                (
                    "target_state=new_schema_conflict"
                    if target_state == "conflict"
                    else None
                ),
                (
                    "new_schema_not_exists=nonexistent_schema"
                    if target_state == "nonexistent"
                    else None
                ),
                (
                    "new_schema_shape=nonexistent_schema"
                    if target_state == "nonexistent"
                    else "new_schema_shape=existing_schema"
                ),
                "verification_mode=pg_aggregate_catalog_query",
                "cleanup_mode=DROP_AGGREGATE_CASCADE",
            ),
            strategy="full conditional Cartesian S14 signatures × 3 aggregate-name shapes × {conflict, nonexistent schema}",
            description=f"Reject ALTER AGGREGATE SET SCHEMA for {target_state} target",
            expected_anchor=f"SQLSTATE {sqlstate} and source aggregate identity unchanged",
        )

    # 12 isolated lookup failures: each action branch traverses each shared
    # object/signature failure so action-specific parse nodes cannot hide it.
    for branch, cause in itertools.product(
        _BRANCHES,
        ("aggregate_not_exists", "wrong_arg_count", "wrong_arg_type", "star_mismatch"),
    ):
        factor = {
            "aggregate_not_exists": "aggregate_not_exists=not_exists",
            "wrong_arg_count": "signature_mismatch=wrong_arg_count",
            "wrong_arg_type": "signature_mismatch=wrong_arg_type",
            "star_mismatch": "star_mismatch=star_for_nonzero_arg",
        }[cause]
        add(
            group="lookup_failure_product",
            case_type="negative",
            outcome="expected_failure",
            axes={
                **_spec_axes(_SIGNATURES[1]),
                "branch": branch,
                "aggregate_name_shape": "schema_qualified",
                "lookup_failure": cause,
                "expected_sqlstate": "42883",
            },
            factor_values=_factor_tokens(
                _branch_token(branch),
                *_signature_tokens(_SIGNATURES[1]),
                "expected_status=failure",
                factor,
                "verification_mode=pg_aggregate_catalog_query",
                "cleanup_mode=DROP_AGGREGATE_IF_EXISTS",
            ),
            strategy="full Cartesian 3 action branches × 4 isolated aggregate lookup failures",
            description=f"Reject ALTER AGGREGATE {branch} for isolated {cause}",
            expected_anchor="SQLSTATE 42883 and any existing control aggregate unchanged",
        )

    # Permission and no-op truth tables from PostgreSQL's objectaddress and
    # namespace checks.  Boolean axes are explicit derived axes, not invented
    # canonical factor values.
    for privilege, has_create in itertools.product(
        ("superuser", "aggregate_owner", "non_owner"), ("yes", "no")
    ):
        success = privilege == "superuser" or (
            privilege == "aggregate_owner" and has_create == "yes"
        )
        add(
            group="rename_schema_privilege_product",
            case_type="permission",
            outcome="success" if success else "expected_failure",
            axes={
                **_spec_axes(_SIGNATURES[1]),
                "branch": "rename",
                "aggregate_name_shape": "schema_qualified",
                "privilege": privilege,
                "schema_create": has_create,
                "new_name_shape": "plain_identifier",
                "expected_sqlstate": "00000" if success else "42501",
            },
            factor_values=_factor_tokens(
                _branch_token("rename"),
                *_signature_tokens(_SIGNATURES[1]),
                f"expected_status={'success' if success else 'failure'}",
                _available_state_token("rename"),
                f"privilege_level={privilege}",
                (
                    "insufficient_privilege=non_owner"
                    if privilege == "non_owner" and not success
                    else None
                ),
                (
                    "insufficient_privilege=no_create_on_schema"
                    if has_create == "no" and not success
                    else None
                ),
                "verification_mode=pg_proc_query",
                "cleanup_mode=DROP_AGGREGATE_IF_EXISTS",
            ),
            strategy="full Cartesian privilege level × current-schema CREATE for RENAME",
            description=f"Verify RENAME privilege truth cell {privilege}/{has_create}",
            expected_anchor=f"SQLSTATE {'00000' if success else '42501'} and privilege-order behavior",
        )

    for privilege, can_set, new_owner_create in itertools.product(
        ("superuser", "aggregate_owner", "non_owner"), ("yes", "no"), ("yes", "no")
    ):
        success = privilege == "superuser" or (
            privilege == "aggregate_owner" and can_set == "yes" and new_owner_create == "yes"
        )
        add(
            group="owner_privilege_truth_product",
            case_type="permission",
            outcome="success" if success else "expected_failure",
            axes={
                **_spec_axes(_SIGNATURES[1]),
                "branch": "owner",
                "aggregate_name_shape": "schema_qualified",
                "owner_shape": "plain_role",
                "privilege": privilege,
                "can_set_role": can_set,
                "new_owner_create": new_owner_create,
                "expected_sqlstate": "00000" if success else "42501",
            },
            factor_values=_factor_tokens(
                _branch_token("owner"),
                *_signature_tokens(_SIGNATURES[1]),
                f"expected_status={'success' if success else 'failure'}",
                (
                    _available_state_token("owner")
                    if success
                    else "target_state=new_owner_unavailable"
                ),
                "new_owner_shape=plain_role",
                f"privilege_level={privilege}",
                (
                    "owner_membership=member_of_new_owner"
                    if can_set == "yes"
                    else "owner_membership=not_member_of_new_owner"
                ),
                (
                    "insufficient_privilege=no_create_on_schema"
                    if new_owner_create == "no" and not success
                    else None
                ),
                (
                    "insufficient_privilege=non_owner"
                    if privilege == "non_owner" and not success
                    else None
                ),
                "verification_mode=pg_proc_query",
                "cleanup_mode=DROP_AGGREGATE_IF_EXISTS",
            ),
            strategy="full Cartesian privilege level × SET ROLE ability × new-owner schema CREATE",
            description=f"Verify OWNER privilege truth cell {privilege}/{can_set}/{new_owner_create}",
            expected_anchor=f"SQLSTATE {'00000' if success else '42501'} and ordered ownership checks",
        )

    for group, same_schema in (
        ("set_schema_privilege_product", "no"),
        ("same_schema_noop_product", "yes"),
    ):
        for privilege, has_create in itertools.product(
            ("superuser", "aggregate_owner", "non_owner"), ("yes", "no")
        ):
            if same_schema == "yes":
                success = privilege == "superuser" or has_create == "yes"
            else:
                success = privilege == "superuser" or (
                    privilege == "aggregate_owner" and has_create == "yes"
                )
            add(
                group=group,
                case_type="permission",
                outcome="success" if success else "expected_failure",
                axes={
                    **_spec_axes(_SIGNATURES[1]),
                    "branch": "set_schema",
                    "aggregate_name_shape": "schema_qualified",
                    "privilege": privilege,
                    "schema_create": has_create,
                    "same_schema": same_schema,
                    "expected_sqlstate": "00000" if success else "42501",
                },
                factor_values=_factor_tokens(
                    _branch_token("set_schema"),
                    *_signature_tokens(_SIGNATURES[1]),
                    f"expected_status={'success' if success else 'failure'}",
                    _available_state_token("set_schema"),
                    "new_schema_shape=existing_schema",
                    f"privilege_level={privilege}",
                    (
                        "insufficient_privilege=no_create_on_schema"
                        if has_create == "no" and not success
                        else None
                    ),
                    (
                        "insufficient_privilege=non_owner"
                        if privilege == "non_owner" and not success
                        else None
                    ),
                    "verification_mode=pg_aggregate_catalog_query",
                    "cleanup_mode=DROP_AGGREGATE_IF_EXISTS",
                ),
                strategy=f"full Cartesian privilege level × schema CREATE for {'same-schema no-op' if same_schema == 'yes' else 'new-schema move'}",
                description=f"Verify SET SCHEMA privilege cell {privilege}/{has_create}/same={same_schema}",
                expected_anchor=f"SQLSTATE {'00000' if success else '42501'} and namespace-check ordering",
            )

    for privilege in ("superuser", "aggregate_owner", "non_owner"):
        add(
            group="same_owner_noop_product",
            case_type="permission",
            outcome="success",
            axes={
                **_spec_axes(_SIGNATURES[1]),
                "branch": "owner",
                "aggregate_name_shape": "schema_qualified",
                "owner_shape": "plain_role",
                "privilege": privilege,
                "same_owner": "yes",
                "expected_sqlstate": "00000",
            },
            factor_values=_factor_tokens(
                _branch_token("owner"),
                *_signature_tokens(_SIGNATURES[1]),
                "expected_status=success",
                _available_state_token("owner"),
                "new_owner_shape=plain_role",
                f"privilege_level={privilege}",
                "verification_mode=pg_proc_query",
                "cleanup_mode=DROP_AGGREGATE_IF_EXISTS",
            ),
            strategy="full privilege-level product for OWNER TO existing owner early no-op",
            description=f"Verify OWNER TO same owner no-op for {privilege}",
            expected_anchor="SQLSTATE 00000 and proowner unchanged even for the non-owner early-return cell",
        )

    for branch, spec in itertools.product(("rename", "set_schema"), _SIGNATURES):
        add(
            group="function_conflict_product",
            case_type="negative",
            outcome="expected_failure",
            axes={
                **_spec_axes(spec),
                "branch": branch,
                "aggregate_name_shape": "schema_qualified",
                "function_conflict": "same_flat_signature",
                "expected_sqlstate": "42723",
            },
            factor_values=_factor_tokens(
                _branch_token(branch),
                *_signature_tokens(spec),
                "expected_status=failure",
                "verification_mode=pg_proc_query",
                "cleanup_mode=DROP_AGGREGATE_CASCADE",
            ),
            strategy="full Cartesian {RENAME, SET SCHEMA} × S14 for ordinary-function namespace conflicts",
            description=f"Reject {branch} collision with ordinary function for {spec.signature_id}",
            expected_anchor="SQLSTATE 42723 and aggregate/function objects both unchanged",
        )

    for system_schema, direction in itertools.product(
        ("pg_temp", "pg_toast"), ("move_into", "move_out")
    ):
        add(
            group="system_schema_boundary_product",
            case_type="negative",
            outcome="expected_failure",
            axes={
                **_spec_axes(_SIGNATURES[1]),
                "branch": "set_schema",
                "aggregate_name_shape": "schema_qualified",
                "system_schema": system_schema,
                "direction": direction,
                "expected_sqlstate": "0A000",
            },
            factor_values=_factor_tokens(
                _branch_token("set_schema"),
                *_signature_tokens(_SIGNATURES[1]),
                "expected_status=failure",
                "verification_mode=pg_aggregate_catalog_query",
                "cleanup_mode=DROP_AGGREGATE_CASCADE",
            ),
            strategy="full Cartesian {pg_temp, pg_toast} × {move into, move out}",
            description=f"Reject ALTER AGGREGATE {direction} {system_schema}",
            expected_anchor="SQLSTATE 0A000 and no system-schema object leakage",
            execution_profile="external_isolated",
        )

    boundary_specs = (
        ("ordered_variadic_missing_pair", "0A000"),
        ("ordered_variadic_extra_aggregated", "0A000"),
        ("ordered_variadic_type_mismatch", "0A000"),
    )
    for branch, (boundary, sqlstate) in itertools.product(_BRANCHES, boundary_specs):
        add(
            group="syntax_type_object_boundary_product",
            case_type="negative",
            outcome="expected_failure",
            axes={
                **_spec_axes(_SIGNATURES[11]),
                "branch": branch,
                "aggregate_name_shape": "schema_qualified",
                "boundary": boundary,
                "expected_sqlstate": sqlstate,
            },
            factor_values=_factor_tokens(
                _branch_token(branch),
                "expected_status=failure",
                "verification_mode=pg_aggregate_catalog_query",
                "cleanup_mode=DROP_AGGREGATE_IF_EXISTS",
            ),
            strategy="3 action branches × 3 invalid ordered-VARIADIC bindings",
            description=f"Reject {branch} boundary {boundary}",
            expected_anchor=f"SQLSTATE {sqlstate} and usable session",
        )

    for branch, mode in itertools.product(_BRANCHES, ("OUT", "INOUT")):
        add(
            group="syntax_type_object_boundary_product",
            case_type="negative",
            outcome="expected_failure",
            axes={
                **_spec_axes(_SIGNATURES[1]),
                "branch": branch,
                "aggregate_name_shape": "schema_qualified",
                "boundary": f"output_mode_{mode.lower()}",
                "output_mode": mode,
                "expected_sqlstate": "0A000",
            },
            factor_values=_factor_tokens(
                _branch_token(branch),
                "expected_status=failure",
                "verification_mode=pg_aggregate_catalog_query",
                "cleanup_mode=DROP_AGGREGATE_IF_EXISTS",
            ),
            strategy="full Cartesian 3 action branches × {OUT, INOUT} forbidden modes",
            description=f"Reject aggregate output mode {mode} for {branch}",
            expected_anchor="SQLSTATE 0A000 and unchanged aggregate",
        )

    for branch, boundary, sqlstate in itertools.product(
        _BRANCHES,
        ("empty_parentheses", "ordered_missing_argument", "unknown_argtype", "ordinary_function_target"),
        ("placeholder",),
    ):
        expected = {
            "empty_parentheses": "42601",
            "ordered_missing_argument": "42601",
            "unknown_argtype": "42704",
            "ordinary_function_target": "42809",
        }[boundary]
        add(
            group="syntax_type_object_boundary_product",
            case_type="negative",
            outcome="expected_failure",
            axes={
                **_spec_axes(_SIGNATURES[1]),
                "branch": branch,
                "aggregate_name_shape": "schema_qualified",
                "boundary": boundary,
                "expected_sqlstate": expected,
            },
            factor_values=_factor_tokens(
                _branch_token(branch),
                "expected_status=failure",
                "verification_mode=pg_aggregate_catalog_query",
                "cleanup_mode=DROP_AGGREGATE_IF_EXISTS",
            ),
            strategy=f"full 3-action product for isolated {boundary} boundary",
            description=f"Reject {branch} boundary {boundary}",
            expected_anchor=f"SQLSTATE {expected} and usable session",
        )

    add(
        group="syntax_type_object_boundary_product",
        case_type="negative",
        outcome="expected_failure",
        axes={
            **_spec_axes(_SIGNATURES[1]),
            "branch": "rename",
            "aggregate_name_shape": "schema_qualified",
            "boundary": "unquoted_reserved_new_name",
            "expected_sqlstate": "42601",
        },
        factor_values=_factor_tokens(
            _branch_token("rename"),
            "expected_status=failure",
            "verification_mode=pg_aggregate_catalog_query",
            "cleanup_mode=DROP_AGGREGATE_IF_EXISTS",
        ),
        strategy="isolated unquoted reserved-word parser boundary",
        description="Reject unquoted reserved word as ALTER AGGREGATE new name",
        expected_anchor="SQLSTATE 42601, distinguishing it from the quoted reserved-word success cells",
    )

    for branch, misplaced in itertools.product(
        _BRANCHES, ("all_arguments_after_order_by", "extra_direct_argument")
    ):
        add(
            group="order_boundary_compatibility_product",
            case_type="compatibility",
            outcome="success",
            axes={
                "signature_id": "s15_order_boundary_compatibility",
                "signature_key": "ordered_set_signature",
                "fixture_kind": "ordered_multi",
                "target_signature": (
                    "ORDER BY double precision, integer, text"
                    if misplaced == "all_arguments_after_order_by"
                    else "double precision, integer ORDER BY text"
                ),
                "aggregate_kind": "o",
                "direct_arg_count": "1",
                "flat_arg_count": "3",
                "branch": branch,
                "aggregate_name_shape": "schema_qualified",
                "order_boundary": misplaced,
                "expected_sqlstate": "00000",
            },
            factor_values=_factor_tokens(
                _branch_token(branch),
                "aggregate_signature=ordered_set_signature",
                "aggregate_form=ordered_set",
                "expected_status=success",
                _available_state_token(branch),
                "verification_mode=pg_aggregate_catalog_query",
                "cleanup_mode=DROP_AGGREGATE_CASCADE",
            ),
            strategy="full Cartesian 3 actions × 2 ORDER BY boundary-misplacement lookup forms",
            description=f"Verify flattened aggregate lookup for {branch}/{misplaced}",
            expected_anchor="SQLSTATE 00000, stable OID predicate, and original aggnumdirectargs preserved",
        )

    if len(cases) != 783:
        raise RemainingStatementRegressError(
            f"ALTER AGGREGATE strict design expected 783 cases, found {len(cases)}"
        )
    return tuple(cases)


def _ids(
    cases: tuple[StatementRegressCase, ...],
    predicate: Callable[[StatementRegressCase], bool],
) -> tuple[str, ...]:
    return tuple(case.case_id for case in cases if predicate(case))


def _factor_decisions(
    entry: StatementCycleEntry,
    cases: tuple[StatementRegressCase, ...],
) -> tuple[FactorValueDecision, ...]:
    expected_failure_values = {
        ("aggregate_not_exists", "not_exists"),
        ("expected_status", "failure"),
        ("insufficient_privilege", "no_create_on_schema"),
        ("insufficient_privilege", "non_owner"),
        ("new_name_conflict", "same_signature_conflict"),
        ("new_owner_not_exists", "nonexistent_role"),
        ("new_schema_not_exists", "nonexistent_schema"),
        ("new_schema_shape", "nonexistent_schema"),
        ("owner_membership", "not_member_of_new_owner"),
        ("privilege_level", "non_owner"),
        ("signature_mismatch", "wrong_arg_count"),
        ("signature_mismatch", "wrong_arg_type"),
        ("star_mismatch", "star_for_nonzero_arg"),
        ("target_state", "new_name_conflict"),
        ("target_state", "new_owner_unavailable"),
        ("target_state", "new_schema_conflict"),
    }
    decisions: list[FactorValueDecision] = []
    for factor in entry.factors:
        for value, row_id in zip(factor.values, factor.row_ids):
            token = f"{factor.name}={value}"
            witnesses = _ids(cases, lambda case, token=token: token in case.factor_values)
            if not witnesses:
                raise RemainingStatementRegressError(
                    f"ALTER AGGREGATE has no real witness for {token}"
                )
            failure = (factor.name, value) in expected_failure_values
            decisions.append(
                FactorValueDecision(
                    row_id=row_id,
                    factor=factor.name,
                    value=value,
                    disposition="expected_failure" if failure else "covered",
                    reason=(
                        "The canonical value is witnessed by isolated expected-failure SQL with a stable SQLSTATE oracle."
                        if failure
                        else None
                    ),
                    case_ids=witnesses,
                )
            )
    return tuple(decisions)


def build_alter_aggregate_plan(
    snapshot: StatementFactorCycleSnapshot,
    entry: StatementCycleEntry,
) -> StatementRegressPlan:
    cases = _build_cases()
    if tuple(case.ordinal for case in cases) != tuple(range(1, 784)):
        raise RemainingStatementRegressError(
            "ALTER AGGREGATE case ordinals are not contiguous"
        )
    return StatementRegressPlan(
        statement_key="alter_aggregate",
        file_prefix="ALTERAGGREGATE",
        cycle_fingerprint=snapshot.fingerprint,
        matrix_path=entry.matrix_path.as_posix(),
        matrix_sha256=entry.matrix_sha256,
        reference_path=entry.reference_path.as_posix(),
        reference_sha256=entry.reference_sha256,
        universe_semantic_sha256=snapshot.universe_semantic_sha256,
        official_source=entry.official_source,
        cases=cases,
        factor_decisions=_factor_decisions(entry, cases),
    )


def _quote_ident(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def _quote_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def _spec_for_case(case: StatementRegressCase) -> AggregateSignatureSpec:
    signature_id = case.derived_axes["signature_id"]
    if signature_id == "s15_order_boundary_compatibility":
        return AggregateSignatureSpec(
            signature_id=signature_id,
            canonical_signature="ordered_set_signature",
            aggregate_form="ordered_set",
            fixture_kind="ordered_multi",
            target_signature=case.derived_axes["target_signature"],
            create_signature=(
                "direct_value double precision ORDER BY "
                "ordered_one integer, ordered_two text"
            ),
            aggregate_kind="o",
            direct_arg_count=1,
            flat_arg_count=3,
        )
    try:
        return _SIGNATURE_BY_ID[signature_id]
    except KeyError as exc:
        raise RemainingStatementRegressError(
            f"unknown ALTER AGGREGATE signature design {signature_id}"
        ) from exc


def _object_names(case: StatementRegressCase) -> dict[str, str]:
    prefix = case.object_prefix
    shape = case.derived_axes.get("aggregate_name_shape", "schema_qualified")
    source_schema = f"{prefix}src"
    target_schema = f"{prefix}dst"
    if shape == "quoted_identifier":
        aggregate_raw = f"{prefix}Aggregate Name"
        unqualified = _quote_ident(aggregate_raw)
    else:
        aggregate_raw = f"{prefix}agg"
        unqualified = aggregate_raw
    qualified = f"{source_schema}.{_quote_ident(aggregate_raw)}"
    target_ref = qualified if shape == "schema_qualified" else unqualified
    new_shape = case.derived_axes.get("new_name_shape", "plain_identifier")
    if new_shape == "quoted_identifier":
        new_raw = f"{prefix}Renamed Aggregate"
        new_ident = _quote_ident(new_raw)
    elif new_shape == "reserved_word":
        new_raw = "select"
        new_ident = '"select"'
    else:
        new_raw = f"{prefix}renamed"
        new_ident = new_raw
    return {
        "prefix": prefix,
        "source_schema": source_schema,
        "target_schema": target_schema,
        "aggregate_raw": aggregate_raw,
        "aggregate_ident": _quote_ident(aggregate_raw),
        "aggregate_qualified": qualified,
        "target_ref": target_ref,
        "new_raw": new_raw,
        "new_ident": new_ident,
        "new_qualified": f"{source_schema}.{new_ident}",
        "target_qualified": f"{target_schema}.{_quote_ident(aggregate_raw)}",
        "actor_role": f"{prefix}actor",
        "old_owner_role": f"{prefix}old_owner",
        "new_owner_role": f"{prefix}new_owner",
        "intruder_role": f"{prefix}intruder",
        "data_table": f"{prefix}data",
        "dependency_view": f"{prefix}dependent_view",
        "temp_sequence": f"{prefix}temp_sequence",
    }


def _flat_routine_types(spec: AggregateSignatureSpec) -> str:
    return {
        "zero": "",
        "single": "integer",
        "multi": "integer, text",
        "ordered": "double precision, integer",
        "ordered_no_direct": "integer",
        "variadic": "integer[]",
        "ordered_variadic": '"any"',
        "hypothetical": "integer, integer",
        "ordered_multi": "double precision, integer, text",
    }[spec.fixture_kind]


def _support_function_lines(
    spec: AggregateSignatureSpec,
    schema: str,
    prefix: str,
) -> list[str]:
    step = f"{schema}.{prefix}step"
    final = f"{schema}.{prefix}final"
    if spec.fixture_kind == "zero":
        return [
            f"CREATE FUNCTION {step}(state bigint) RETURNS bigint",
            "LANGUAGE sql IMMUTABLE",
            "AS 'SELECT state + 1';",
        ]
    if spec.fixture_kind == "single":
        return [
            f"CREATE FUNCTION {step}(state bigint, value integer) RETURNS bigint",
            "LANGUAGE sql IMMUTABLE",
            "AS 'SELECT state + COALESCE(value, 0)';",
        ]
    if spec.fixture_kind == "multi":
        return [
            f"CREATE FUNCTION {step}(state bigint, value integer, note text) RETURNS bigint",
            "LANGUAGE sql IMMUTABLE",
            "AS 'SELECT state + COALESCE(value, 0) + length(COALESCE(note, ''''))';",
        ]
    if spec.fixture_kind == "variadic":
        return [
            f"CREATE FUNCTION {step}(state bigint, VARIADIC items integer[]) RETURNS bigint",
            "LANGUAGE sql IMMUTABLE",
            "AS 'SELECT state + COALESCE((SELECT sum(item) FROM unnest(items) AS item), 0)';",
        ]
    if spec.fixture_kind in {"ordered", "hypothetical"}:
        direct_type = "double precision" if spec.fixture_kind == "ordered" else "integer"
        final_type = "double precision" if spec.fixture_kind == "ordered" else "bigint"
        final_expr = (
            "state::double precision + direct_value"
            if spec.fixture_kind == "ordered"
            else "state + direct_value"
        )
        return [
            f"CREATE FUNCTION {step}(state bigint, ordered_value integer) RETURNS bigint",
            "LANGUAGE sql IMMUTABLE",
            "AS 'SELECT state + COALESCE(ordered_value, 0)';",
            f"CREATE FUNCTION {final}(state bigint, direct_value {direct_type}) RETURNS {final_type}",
            "LANGUAGE sql IMMUTABLE",
            f"AS 'SELECT {final_expr}';",
        ]
    if spec.fixture_kind == "ordered_no_direct":
        return [
            f"CREATE FUNCTION {step}(state bigint, ordered_value integer) RETURNS bigint",
            "LANGUAGE sql IMMUTABLE",
            "AS 'SELECT state + COALESCE(ordered_value, 0)';",
        ]
    if spec.fixture_kind == "ordered_multi":
        return [
            f"CREATE FUNCTION {step}(state bigint, ordered_value integer, ordered_note text) RETURNS bigint",
            "LANGUAGE sql IMMUTABLE",
            "AS 'SELECT state + COALESCE(ordered_value, 0) + length(COALESCE(ordered_note, ''''))';",
            f"CREATE FUNCTION {final}(state bigint, direct_value double precision) RETURNS double precision",
            "LANGUAGE sql IMMUTABLE",
            "AS 'SELECT state::double precision + direct_value';",
        ]
    if spec.fixture_kind == "ordered_variadic":
        return []
    raise RemainingStatementRegressError(
        f"no support-function fixture for {spec.fixture_kind}"
    )


def _create_aggregate_lines(
    spec: AggregateSignatureSpec,
    *,
    schema: str,
    aggregate_ident: str,
    support_schema: str,
    prefix: str,
) -> list[str]:
    target = f"{schema}.{aggregate_ident}"
    step = f"{support_schema}.{prefix}step"
    final = f"{support_schema}.{prefix}final"
    if spec.fixture_kind == "ordered_variadic":
        return [
            f"CREATE AGGREGATE {target}({spec.create_signature}) (",
            "    STYPE = internal,",
            "    SFUNC = pg_catalog.ordered_set_transition_multi,",
            "    FINALFUNC = pg_catalog.rank_final,",
            "    FINALFUNC_EXTRA = true,",
            "    HYPOTHETICAL",
            ");",
        ]
    options = [
        f"    SFUNC = {step},",
        "    STYPE = bigint,",
    ]
    if spec.fixture_kind in {"ordered", "hypothetical", "ordered_multi"}:
        options.append(f"    FINALFUNC = {final},")
    options.append("    INITCOND = '0'")
    if spec.fixture_kind == "hypothetical":
        options[-1] += ","
        options.append("    HYPOTHETICAL")
    return [
        f"CREATE AGGREGATE {target}({spec.create_signature}) (",
        *options,
        ");",
    ]


def _fixture_lines(
    spec: AggregateSignatureSpec,
    names: Mapping[str, str],
    *,
    schema: str | None = None,
    aggregate_ident: str | None = None,
    support_schema: str | None = None,
    create_support: bool = True,
) -> list[str]:
    schema = schema or names["source_schema"]
    support_schema = support_schema or names["source_schema"]
    aggregate_ident = aggregate_ident or names["aggregate_ident"]
    lines: list[str] = []
    if create_support:
        lines.extend(
            _support_function_lines(spec, support_schema, names["prefix"])
        )
    lines.extend(
        _create_aggregate_lines(
            spec,
            schema=schema,
            aggregate_ident=aggregate_ident,
            support_schema=support_schema,
            prefix=names["prefix"],
        )
    )
    return lines


def _table_setup_lines(names: Mapping[str, str]) -> list[str]:
    table = f"public.{names['data_table']}"
    return [
        f"CREATE TABLE {table} (",
        "    id integer PRIMARY KEY,",
        "    group_key text NOT NULL,",
        "    input_one integer NOT NULL CHECK (input_one > 0),",
        "    input_two integer NOT NULL CHECK (input_two > 0),",
        "    note text NOT NULL CHECK (length(note) > 0),",
        "    CONSTRAINT " + names["prefix"] + "data_unique UNIQUE (group_key, id)",
        ");",
        f"INSERT INTO {table}(id, group_key, input_one, input_two, note) VALUES",
        "    (1, 'g1', 1, 10, 'a'),",
        "    (2, 'g1', 2, 20, 'bb'),",
        "    (3, 'g2', 3, 30, 'ccc');",
    ]


def _aggregate_call(
    spec: AggregateSignatureSpec,
    aggregate_qualified: str,
    names: Mapping[str, str],
) -> tuple[str, str]:
    table = f"public.{names['data_table']}"
    if spec.fixture_kind == "zero":
        return f"{aggregate_qualified}(*)", "3::bigint"
    if spec.fixture_kind == "single":
        return f"{aggregate_qualified}(input_one)", "6::bigint"
    if spec.fixture_kind == "multi":
        return f"{aggregate_qualified}(input_one, note)", "12::bigint"
    if spec.fixture_kind == "variadic":
        return f"{aggregate_qualified}(input_one, input_two)", "66::bigint"
    if spec.fixture_kind == "ordered":
        return (
            f"{aggregate_qualified}(10.0::double precision) WITHIN GROUP (ORDER BY input_one)",
            "16.0::double precision",
        )
    if spec.fixture_kind == "ordered_no_direct":
        return (
            f"{aggregate_qualified}() WITHIN GROUP (ORDER BY input_one)",
            "6::bigint",
        )
    if spec.fixture_kind == "ordered_variadic":
        return (
            f"{aggregate_qualified}(3) WITHIN GROUP (ORDER BY input_one)",
            "3::bigint",
        )
    if spec.fixture_kind == "hypothetical":
        return (
            f"{aggregate_qualified}(10) WITHIN GROUP (ORDER BY input_one)",
            "16::bigint",
        )
    if spec.fixture_kind == "ordered_multi":
        return (
            f"{aggregate_qualified}(10.0::double precision) WITHIN GROUP (ORDER BY input_one, note)",
            "22.0::double precision",
        )
    raise RemainingStatementRegressError(
        f"no aggregate execution oracle for {spec.fixture_kind}"
    )


def _capture_oid_lines(
    names: Mapping[str, str],
    *,
    schema: str,
    raw_name: str,
    variable: str = "before_oid",
) -> list[str]:
    namespace_predicate = (
        "n.oid = pg_catalog.pg_my_temp_schema()"
        if schema == "pg_temp"
        else f"n.nspname = {_quote_literal(schema)}"
    )
    return [
        f"SELECT p.oid::text AS {variable}",
        "FROM pg_catalog.pg_proc AS p",
        "JOIN pg_catalog.pg_namespace AS n ON n.oid = p.pronamespace",
        f"WHERE {namespace_predicate}",
        f"  AND p.proname = {_quote_literal(raw_name)}",
        "  AND p.prokind = 'a'",
        "ORDER BY p.oid",
        r"\gset",
    ]


def _catalog_oracle_lines(
    spec: AggregateSignatureSpec,
    *,
    schema: str,
    raw_name: str,
    oid_variable: str | None,
    label: str,
) -> list[str]:
    oid_predicate = (
        f"COALESCE(bool_and(p.oid::text = :'{oid_variable}'), false)"
        if oid_variable
        else "true"
    )
    namespace_predicate = (
        "n.oid = pg_catalog.pg_my_temp_schema()"
        if schema == "pg_temp"
        else f"n.nspname = {_quote_literal(schema)}"
    )
    return [
        "SELECT",
        f"    count(*) = 1 AS {label}_present,",
        f"    {oid_predicate} AS {label}_oid_stable,",
        f"    COALESCE(bool_and(a.aggkind = {_quote_literal(spec.aggregate_kind)}), false) AS {label}_kind_stable,",
        f"    COALESCE(bool_and(a.aggnumdirectargs = {spec.direct_arg_count}), false) AS {label}_direct_count_stable,",
        f"    COALESCE(bool_and(p.pronargs = {spec.flat_arg_count}), false) AS {label}_arity_stable",
        "FROM pg_catalog.pg_proc AS p",
        "JOIN pg_catalog.pg_namespace AS n ON n.oid = p.pronamespace",
        "JOIN pg_catalog.pg_aggregate AS a ON a.aggfnoid = p.oid",
        f"WHERE {namespace_predicate}",
        f"  AND p.proname = {_quote_literal(raw_name)}",
        "  AND p.prokind = 'a'",
        f"ORDER BY {label}_present, {label}_oid_stable, {label}_kind_stable, {label}_direct_count_stable, {label}_arity_stable;",
    ]


def _routine_owner_setup(
    spec: AggregateSignatureSpec,
    names: Mapping[str, str],
    owner: str,
) -> str:
    return (
        f"ALTER ROUTINE {names['aggregate_qualified']}"
        f"({_flat_routine_types(spec)}) OWNER TO {owner};"
    )


def _target_action(
    case: StatementRegressCase,
    spec: AggregateSignatureSpec,
    names: Mapping[str, str],
    *,
    target_signature: str | None = None,
) -> str:
    signature = target_signature if target_signature is not None else case.derived_axes["target_signature"]
    reference = names["target_ref"]
    branch = case.derived_axes["branch"]
    if branch == "rename":
        new_name = names["new_ident"]
        if case.derived_axes.get("boundary") == "unquoted_reserved_new_name":
            new_name = "select"
        return f"ALTER AGGREGATE {reference}({signature}) RENAME TO {new_name};"
    if branch == "owner":
        owner_shape = case.derived_axes.get("owner_shape", "plain_role")
        owner = (
            names["new_owner_role"] if owner_shape == "plain_role" else owner_shape
        )
        return f"ALTER AGGREGATE {reference}({signature}) OWNER TO {owner};"
    target_schema = (
        names["source_schema"]
        if case.derived_axes.get("same_schema") == "yes"
        else names["target_schema"]
    )
    return f"ALTER AGGREGATE {reference}({signature}) SET SCHEMA {target_schema};"


def _roles_cleanup_lines(names: Mapping[str, str]) -> list[str]:
    return [
        "RESET ROLE;",
        "RESET SESSION AUTHORIZATION;",
        (
            "DROP ROLE IF EXISTS "
            + ", ".join(
                (
                    names["actor_role"],
                    names["intruder_role"],
                    names["old_owner_role"],
                    names["new_owner_role"],
                )
            )
            + ";"
        ),
    ]


def _base_precleanup_lines(
    names: Mapping[str, str],
    *,
    table_based: bool,
) -> list[str]:
    lines: list[str] = []
    if table_based:
        lines.append(f"DROP TABLE IF EXISTS public.{names['data_table']} CASCADE;")
    lines.extend(
        [
            "RESET ROLE;",
            "RESET SESSION AUTHORIZATION;",
            "SET client_min_messages TO warning;",
            r"\set ON_ERROR_STOP on",
            f"DROP SCHEMA IF EXISTS {names['target_schema']} CASCADE;",
            f"DROP SCHEMA IF EXISTS {names['source_schema']} CASCADE;",
            *_roles_cleanup_lines(names),
            f"CREATE SCHEMA {names['source_schema']};",
            f"SET search_path TO {names['source_schema']}, pg_catalog;",
        ]
    )
    return lines


def _ordinary_function_lines(
    spec: AggregateSignatureSpec,
    *,
    schema: str,
    function_ident: str,
) -> list[str]:
    types = _flat_routine_types(spec)
    if spec.fixture_kind == "ordered_variadic":
        return [
            f"CREATE FUNCTION {schema}.{function_ident}(VARIADIC \"any\") RETURNS bigint",
            "LANGUAGE internal IMMUTABLE",
            "AS 'hypothetical_rank_final';",
        ]
    return [
        f"CREATE FUNCTION {schema}.{function_ident}({types}) RETURNS integer",
        "LANGUAGE sql IMMUTABLE",
        "AS 'SELECT 1';",
    ]


def _expected_final_identity(
    case: StatementRegressCase,
    names: Mapping[str, str],
) -> tuple[str, str]:
    group = case.case_group
    branch = case.derived_axes["branch"]
    if group == "success_rename_product" or (
        group in {"rename_schema_privilege_product", "order_boundary_compatibility_product"}
        and branch == "rename"
        and case.outcome == "success"
    ):
        return names["source_schema"], names["new_raw"]
    if branch == "set_schema" and case.outcome == "success" and case.derived_axes.get("same_schema") != "yes":
        return names["target_schema"], names["aggregate_raw"]
    return names["source_schema"], names["aggregate_raw"]


def _render_system_schema_case(
    plan: StatementRegressPlan,
    case: StatementRegressCase,
    spec: AggregateSignatureSpec,
    names: Mapping[str, str],
) -> str:
    system_schema = case.derived_axes["system_schema"]
    direction = case.derived_axes["direction"]
    source_schema = names["source_schema"] if direction == "move_into" else system_schema
    target_schema = system_schema if direction == "move_into" else names["target_schema"]
    aggregate_ident = names["aggregate_ident"]
    aggregate_ref = f"{source_schema}.{aggregate_ident}"
    lines = _header(plan, case) + [
        "-- 1. 清理本编号普通 schema、角色和可能残留的系统 schema 测试对象。",
        "RESET ROLE;",
        "RESET SESSION AUTHORIZATION;",
        "SET client_min_messages TO warning;",
        r"\set ON_ERROR_STOP on",
        f"DROP SCHEMA IF EXISTS {names['target_schema']} CASCADE;",
        f"DROP SCHEMA IF EXISTS {names['source_schema']} CASCADE;",
    ]
    if system_schema == "pg_temp":
        lines.extend(
            [
                f"CREATE TEMP SEQUENCE IF NOT EXISTS {names['temp_sequence']};",
                f"DROP AGGREGATE IF EXISTS pg_temp.{aggregate_ident}(integer) CASCADE;",
                f"DROP FUNCTION IF EXISTS pg_temp.{names['prefix']}step(bigint, integer) CASCADE;",
            ]
        )
    else:
        lines.extend(
            [
                f"DROP AGGREGATE IF EXISTS pg_toast.{aggregate_ident}(integer) CASCADE;",
                f"DROP FUNCTION IF EXISTS pg_toast.{names['prefix']}step(bigint, integer) CASCADE;",
            ]
        )
    lines.extend(
        [
            "",
            "-- 2. 在移动源 schema 建立完整 support function 与单参数聚合 fixture。",
            (
                f"CREATE SCHEMA {names['source_schema']};"
                if direction == "move_into"
                else f"CREATE SCHEMA {names['target_schema']};"
            ),
        ]
    )
    lines.extend(
        _support_function_lines(spec, source_schema, names["prefix"])
    )
    lines.extend(
        _create_aggregate_lines(
            spec,
            schema=source_schema,
            aggregate_ident=aggregate_ident,
            support_schema=source_schema,
            prefix=names["prefix"],
        )
    )
    lines.extend(
        [
            "",
            "-- 3. 保存源对象 OID，仅在后续布尔比较中使用，避免输出不稳定标识。",
            *_capture_oid_lines(
                names,
                schema=source_schema,
                raw_name=names["aggregate_raw"],
            ),
            "",
            f"-- 4. 执行唯一目标 SET SCHEMA {target_schema}；expected SQLSTATE 0A000。",
            r"\set ON_ERROR_STOP off",
            f"ALTER AGGREGATE {aggregate_ref}(integer) SET SCHEMA {target_schema};",
            r"\echo target_sqlstate :SQLSTATE",
            "SELECT :'SQLSTATE' = '0A000' AS target_sqlstate_matches;",
            r"\set ON_ERROR_STOP on",
            "",
            "-- 5. 确认失败后源聚合仍在原 namespace，且 OID、kind、arity 均未改变。",
            *_catalog_oracle_lines(
                spec,
                schema=source_schema,
                raw_name=names["aggregate_raw"],
                oid_variable="before_oid",
                label="source_aggregate",
            ),
            "",
            "-- 6. 显式删除系统 schema 中的编号对象，避免污染后续文件。",
            f"DROP AGGREGATE IF EXISTS {aggregate_ref}(integer) CASCADE;",
            f"DROP FUNCTION IF EXISTS {source_schema}.{names['prefix']}step(bigint, integer) CASCADE;",
            "",
            "-- 7. 反向清理普通 schema 与临时序列，并给出稳定完成锚点。",
            f"DROP SCHEMA IF EXISTS {names['target_schema']} CASCADE;",
            f"DROP SCHEMA IF EXISTS {names['source_schema']} CASCADE;",
        ]
    )
    if system_schema == "pg_temp":
        lines.append(f"DROP SEQUENCE IF EXISTS pg_temp.{names['temp_sequence']};")
    lines.extend(["RESET ALL;", "SELECT true AS cleanup_complete;"])
    return "\n".join(lines).rstrip() + "\n"


def _render_regular_case(
    plan: StatementRegressPlan,
    case: StatementRegressCase,
    spec: AggregateSignatureSpec,
    names: Mapping[str, str],
) -> str:
    group = case.case_group
    axes = case.derived_axes
    table_based = group in {
        "success_rename_product",
        "success_owner_product",
        "success_set_schema_product",
    }
    create_fixture = not (
        group == "lookup_failure_product"
        and axes["lookup_failure"] == "aggregate_not_exists"
    )
    if group == "syntax_type_object_boundary_product" and axes.get("boundary") == "ordinary_function_target":
        create_fixture = False

    lines = _header(plan, case) + [
        "-- 1. 幂等清理本编号对象；角色、schema 和关系均只属于当前文件。",
        *_base_precleanup_lines(names, table_based=table_based),
    ]
    if table_based:
        lines.extend(_table_setup_lines(names))

    lines.extend(
        [
            "",
            "-- 2. 创建完整 support function 与用户自定义聚合；不修改任何内置聚合。",
        ]
    )
    if create_fixture:
        lines.extend(_fixture_lines(spec, names))
        lines.extend(
            [
                *_capture_oid_lines(
                    names,
                    schema=names["source_schema"],
                    raw_name=names["aggregate_raw"],
                )
            ]
        )
    else:
        lines.append("SELECT true AS no_aggregate_fixture_required;")

    context: list[str] = []
    target_signature: str | None = None
    extra_oracle: list[str] = []

    if group == "success_owner_product":
        if axes["owner_shape"] == "plain_role":
            context.extend(
                [
                    f"CREATE ROLE {names['new_owner_role']} NOLOGIN;",
                    f"GRANT CREATE ON SCHEMA {names['source_schema']} TO {names['new_owner_role']};",
                ]
            )
    elif group == "success_set_schema_product":
        context.append(f"CREATE SCHEMA {names['target_schema']};")
    elif group == "failure_rename_conflict_product":
        context.extend(
            _fixture_lines(
                spec,
                names,
                schema=names["source_schema"],
                aggregate_ident=names["new_ident"],
                create_support=False,
            )
        )
    elif group == "failure_owner_unavailable_product":
        reason = axes["unavailable_reason"]
        if reason == "nonexistent_role":
            context.append(
                f"DROP ROLE IF EXISTS {names['new_owner_role']};"
            )
        else:
            context.extend(
                [
                    f"CREATE ROLE {names['actor_role']} NOLOGIN;",
                    f"CREATE ROLE {names['new_owner_role']} NOLOGIN;",
                    f"GRANT USAGE ON SCHEMA {names['source_schema']} TO {names['actor_role']};",
                    _routine_owner_setup(spec, names, names["actor_role"]),
                ]
            )
            if reason == "cannot_set_role":
                context.append(
                    f"GRANT CREATE ON SCHEMA {names['source_schema']} TO {names['new_owner_role']};"
                )
            else:
                context.append(
                    f"GRANT {names['new_owner_role']} TO {names['actor_role']} WITH SET TRUE;"
                )
            context.append(f"SET ROLE {names['actor_role']};")
    elif group == "failure_set_schema_state_product":
        if axes["target_state"] == "conflict":
            context.append(f"CREATE SCHEMA {names['target_schema']};")
            context.extend(
                _fixture_lines(
                    spec,
                    names,
                    schema=names["target_schema"],
                    aggregate_ident=names["aggregate_ident"],
                    create_support=False,
                )
            )
        else:
            context.append(
                f"DROP SCHEMA IF EXISTS {names['target_schema']} CASCADE;"
            )
    elif group == "lookup_failure_product":
        cause = axes["lookup_failure"]
        target_signature = {
            "aggregate_not_exists": spec.target_signature,
            "wrong_arg_count": "integer, text",
            "wrong_arg_type": "text",
            "star_mismatch": "*",
        }[cause]
        if cause == "aggregate_not_exists":
            # Use a distinct missing name without introducing a second failure.
            missing_raw = f"{names['prefix']}missing_aggregate"
            names = dict(names)
            names["aggregate_raw"] = missing_raw
            names["aggregate_ident"] = _quote_ident(missing_raw)
            names["aggregate_qualified"] = (
                f"{names['source_schema']}.{_quote_ident(missing_raw)}"
            )
            names["target_ref"] = names["aggregate_qualified"]
        if axes["branch"] == "owner":
            context.extend(
                [
                    f"CREATE ROLE {names['new_owner_role']} NOLOGIN;",
                    f"GRANT CREATE ON SCHEMA {names['source_schema']} TO {names['new_owner_role']};",
                ]
            )
        elif axes["branch"] == "set_schema":
            context.append(f"CREATE SCHEMA {names['target_schema']};")
    elif group == "rename_schema_privilege_product":
        privilege = axes["privilege"]
        has_create = axes["schema_create"] == "yes"
        if privilege == "superuser":
            context.extend(
                [
                    f"CREATE ROLE {names['old_owner_role']} NOLOGIN;",
                    _routine_owner_setup(spec, names, names["old_owner_role"]),
                ]
            )
        else:
            context.extend(
                [
                    f"CREATE ROLE {names['actor_role']} NOLOGIN;",
                    f"CREATE ROLE {names['old_owner_role']} NOLOGIN;",
                    f"GRANT USAGE ON SCHEMA {names['source_schema']} TO {names['actor_role']};",
                ]
            )
            owner = names["actor_role"] if privilege == "aggregate_owner" else names["old_owner_role"]
            context.append(_routine_owner_setup(spec, names, owner))
            if has_create:
                context.append(
                    f"GRANT CREATE ON SCHEMA {names['source_schema']} TO {names['actor_role']};"
                )
            context.append(f"SET ROLE {names['actor_role']};")
    elif group == "owner_privilege_truth_product":
        privilege = axes["privilege"]
        context.extend(
            [
                f"CREATE ROLE {names['actor_role']} NOLOGIN;",
                f"CREATE ROLE {names['old_owner_role']} NOLOGIN;",
                f"CREATE ROLE {names['new_owner_role']} NOLOGIN;",
            ]
        )
        if privilege == "superuser":
            context.append(_routine_owner_setup(spec, names, names["old_owner_role"]))
        else:
            owner = names["actor_role"] if privilege == "aggregate_owner" else names["old_owner_role"]
            context.extend(
                [
                    f"GRANT USAGE ON SCHEMA {names['source_schema']} TO {names['actor_role']};",
                    _routine_owner_setup(spec, names, owner),
                ]
            )
        if axes["can_set_role"] == "yes":
            context.append(
                f"GRANT {names['new_owner_role']} TO {names['actor_role']} WITH SET TRUE;"
            )
        if axes["new_owner_create"] == "yes":
            context.append(
                f"GRANT CREATE ON SCHEMA {names['source_schema']} TO {names['new_owner_role']};"
            )
        if privilege != "superuser":
            context.append(f"SET ROLE {names['actor_role']};")
    elif group in {"set_schema_privilege_product", "same_schema_noop_product"}:
        privilege = axes["privilege"]
        has_create = axes["schema_create"] == "yes"
        if axes["same_schema"] == "no":
            context.append(f"CREATE SCHEMA {names['target_schema']};")
            privilege_schema = names["target_schema"]
        else:
            privilege_schema = names["source_schema"]
        if privilege == "superuser":
            context.extend(
                [
                    f"CREATE ROLE {names['old_owner_role']} NOLOGIN;",
                    _routine_owner_setup(spec, names, names["old_owner_role"]),
                ]
            )
        else:
            context.extend(
                [
                    f"CREATE ROLE {names['actor_role']} NOLOGIN;",
                    f"CREATE ROLE {names['old_owner_role']} NOLOGIN;",
                    f"GRANT USAGE ON SCHEMA {names['source_schema']} TO {names['actor_role']};",
                    f"GRANT USAGE ON SCHEMA {privilege_schema} TO {names['actor_role']};",
                ]
            )
            owner = names["actor_role"] if privilege == "aggregate_owner" else names["old_owner_role"]
            context.append(_routine_owner_setup(spec, names, owner))
            if has_create:
                context.append(
                    f"GRANT CREATE ON SCHEMA {privilege_schema} TO {names['actor_role']};"
                )
            context.append(f"SET ROLE {names['actor_role']};")
    elif group == "same_owner_noop_product":
        privilege = axes["privilege"]
        context.extend(
            [
                f"CREATE ROLE {names['old_owner_role']} NOLOGIN;",
                f"CREATE ROLE {names['intruder_role']} NOLOGIN;",
                f"GRANT USAGE ON SCHEMA {names['source_schema']} TO {names['old_owner_role']};",
                f"GRANT USAGE ON SCHEMA {names['source_schema']} TO {names['intruder_role']};",
                _routine_owner_setup(spec, names, names["old_owner_role"]),
            ]
        )
        names = dict(names)
        names["new_owner_role"] = names["old_owner_role"]
        if privilege == "aggregate_owner":
            context.append(f"SET ROLE {names['old_owner_role']};")
        elif privilege == "non_owner":
            context.append(f"SET ROLE {names['intruder_role']};")
    elif group == "function_conflict_product":
        if axes["branch"] == "rename":
            context.extend(
                _ordinary_function_lines(
                    spec,
                    schema=names["source_schema"],
                    function_ident=names["new_ident"],
                )
            )
        else:
            context.append(f"CREATE SCHEMA {names['target_schema']};")
            context.extend(
                _ordinary_function_lines(
                    spec,
                    schema=names["target_schema"],
                    function_ident=names["aggregate_ident"],
                )
            )
    elif group == "syntax_type_object_boundary_product":
        boundary = axes["boundary"]
        if boundary == "ordinary_function_target":
            context.extend(
                _ordinary_function_lines(
                    _SIGNATURES[1],
                    schema=names["source_schema"],
                    function_ident=names["aggregate_ident"],
                )
            )
        if axes["branch"] == "owner":
            context.extend(
                [
                    f"CREATE ROLE {names['new_owner_role']} NOLOGIN;",
                    f"GRANT CREATE ON SCHEMA {names['source_schema']} TO {names['new_owner_role']};",
                ]
            )
        elif axes["branch"] == "set_schema":
            context.append(f"CREATE SCHEMA {names['target_schema']};")
        if boundary.startswith("ordered_variadic_"):
            target_signature = {
                "ordered_variadic_missing_pair": 'VARIADIC "any" ORDER BY integer',
                "ordered_variadic_extra_aggregated": 'VARIADIC "any" ORDER BY VARIADIC "any", integer',
                "ordered_variadic_type_mismatch": 'VARIADIC "any" ORDER BY VARIADIC integer[]',
            }[boundary]
        elif boundary.startswith("output_mode_"):
            target_signature = f"{axes['output_mode']} integer"
        elif boundary == "empty_parentheses":
            target_signature = ""
        elif boundary == "ordered_missing_argument":
            target_signature = "integer ORDER BY"
        elif boundary == "unknown_argtype":
            target_signature = f"{names['prefix']}missing_type"
        elif boundary == "ordinary_function_target":
            target_signature = "integer"
    elif group == "order_boundary_compatibility_product":
        if axes["branch"] == "owner":
            context.extend(
                [
                    f"CREATE ROLE {names['new_owner_role']} NOLOGIN;",
                    f"GRANT CREATE ON SCHEMA {names['source_schema']} TO {names['new_owner_role']};",
                ]
            )
        elif axes["branch"] == "set_schema":
            context.append(f"CREATE SCHEMA {names['target_schema']};")

    cleanup_mode = axes.get("cleanup_mode")
    dependency_created = table_based and cleanup_mode == "DROP_AGGREGATE_CASCADE"
    if dependency_created:
        call, _ = _aggregate_call(spec, names["aggregate_qualified"], names)
        context.extend(
            [
                f"CREATE VIEW public.{names['dependency_view']} AS",
                f"SELECT {call} AS aggregate_result",
                f"FROM public.{names['data_table']};",
            ]
        )

    lines.extend(
        [
            "",
            "-- 3. 建立本格唯一的目标状态、权限或冲突前置条件。",
            *context,
            "SELECT true AS target_context_ready;",
            "",
            f"-- 4. 执行唯一目标 ALTER AGGREGATE；expected SQLSTATE {axes['expected_sqlstate']}。",
            r"\set ON_ERROR_STOP off",
        ]
    )
    target_sql = _target_action(
        case, spec, names, target_signature=target_signature
    )
    lines.extend(
        [
            target_sql,
            r"\echo target_sqlstate :SQLSTATE",
            f"SELECT :'SQLSTATE' = {_quote_literal(axes['expected_sqlstate'])} AS target_sqlstate_matches;",
            r"\set ON_ERROR_STOP on",
            "RESET ROLE;",
            "",
            "-- 5. 用 schema、prokind、aggkind、direct 参数数、arity 和保存的 OID 验证结果。",
        ]
    )

    if create_fixture:
        final_schema, final_raw = _expected_final_identity(case, names)
        lines.extend(
            _catalog_oracle_lines(
                spec,
                schema=final_schema,
                raw_name=final_raw,
                oid_variable="before_oid",
                label="target_aggregate",
            )
        )
        if axes["branch"] == "owner" and case.outcome == "success":
            if group == "same_owner_noop_product":
                expected_owner = names["old_owner_role"]
                owner_predicate = _quote_literal(expected_owner)
            elif axes.get("owner_shape", "plain_role") == "plain_role":
                owner_predicate = _quote_literal(names["new_owner_role"])
            else:
                owner_predicate = "session_user"
            lines.extend(
                [
                    "SELECT count(*) = 1 AS owner_matches",
                    "FROM pg_catalog.pg_proc AS p",
                    "JOIN pg_catalog.pg_namespace AS n ON n.oid = p.pronamespace",
                    f"WHERE n.nspname = {_quote_literal(final_schema)}",
                    f"  AND p.proname = {_quote_literal(final_raw)}",
                    "  AND p.prokind = 'a'",
                    f"  AND pg_catalog.pg_get_userbyid(p.proowner) = {owner_predicate}",
                    "ORDER BY owner_matches;",
                ]
            )
    else:
        lines.extend(
            [
                "SELECT count(*) = 0 AS aggregate_remains_absent",
                "FROM pg_catalog.pg_proc AS p",
                "JOIN pg_catalog.pg_namespace AS n ON n.oid = p.pronamespace",
                f"WHERE n.nspname = {_quote_literal(names['source_schema'])}",
                f"  AND p.proname = {_quote_literal(names['aggregate_raw'])}",
                "  AND p.prokind = 'a'",
                "ORDER BY aggregate_remains_absent;",
            ]
        )

    lines.extend(
        [
            "",
            "-- 6. 成功主积执行修改后的聚合；失败格只做独立会话可用性和不变性锚定。",
        ]
    )
    if table_based:
        final_schema, final_raw = _expected_final_identity(case, names)
        final_qualified = f"{final_schema}.{_quote_ident(final_raw)}"
        call, expected = _aggregate_call(spec, final_qualified, names)
        lines.extend(
            [
                f"SELECT {call} = {expected} AS aggregate_execution_matches",
                f"FROM public.{names['data_table']};",
            ]
        )
        if dependency_created:
            lines.extend(
                [
                    f"SELECT aggregate_result = {expected} AS dependency_view_still_works",
                    f"FROM public.{names['dependency_view']}",
                    "ORDER BY dependency_view_still_works;",
                ]
            )
    else:
        lines.append("SELECT true AS session_usable_after_target;")

    lines.extend(
        [
            "",
            "-- 7. 按实际最终 identity 反向清理 aggregate、support functions、schema、role 与输入表。",
            "RESET ROLE;",
            "RESET SESSION AUTHORIZATION;",
        ]
    )
    if table_based:
        final_schema, final_raw = _expected_final_identity(case, names)
        final_ref = f"{final_schema}.{_quote_ident(final_raw)}"
        cleanup_signature = spec.create_signature
        if cleanup_mode == "DROP_AGGREGATE":
            lines.append(
                f"DROP AGGREGATE {final_ref}({cleanup_signature});"
            )
        elif cleanup_mode == "DROP_AGGREGATE_IF_EXISTS":
            lines.extend(
                [
                    f"DROP AGGREGATE IF EXISTS {final_ref}({cleanup_signature});",
                    f"DROP AGGREGATE IF EXISTS {final_ref}({cleanup_signature});",
                ]
            )
        else:
            lines.extend(
                [
                    f"DROP AGGREGATE {final_ref}({cleanup_signature}) CASCADE;",
                    f"SELECT to_regclass({_quote_literal('public.' + names['dependency_view'])}) IS NULL AS cascade_dependency_removed;",
                ]
            )
    elif group == "function_conflict_product":
        # The colliding target is deliberately an ordinary function.  Calling
        # DROP AGGREGATE on it would correctly fail with WRONG_OBJECT_TYPE and
        # would turn a valid target assertion into a cleanup failure.  The
        # numbered schema CASCADE below removes the function after the real
        # source aggregate is dropped explicitly.
        lines.append(
            f"DROP AGGREGATE IF EXISTS {names['aggregate_qualified']}({spec.create_signature}) CASCADE;"
        )
    elif (
        group == "syntax_type_object_boundary_product"
        and axes.get("boundary") == "ordinary_function_target"
    ):
        # This case intentionally contains no aggregate.  The numbered source
        # schema CASCADE below is the type-correct cleanup for its function.
        lines.append("SELECT true AS ordinary_function_cleanup_deferred;")
    else:
        # Idempotent fallback cleanup is intentionally broader than the target
        # state: failed rename/schema cases can leave both identities present.
        lines.extend(
            [
                f"DROP AGGREGATE IF EXISTS {names['new_qualified']}({spec.create_signature}) CASCADE;",
                f"DROP AGGREGATE IF EXISTS {names['target_qualified']}({spec.create_signature}) CASCADE;",
                f"DROP AGGREGATE IF EXISTS {names['aggregate_qualified']}({spec.create_signature}) CASCADE;",
            ]
        )
    lines.extend(
        [
            f"DROP SCHEMA IF EXISTS {names['target_schema']} CASCADE;",
            f"DROP SCHEMA IF EXISTS {names['source_schema']} CASCADE;",
            *_roles_cleanup_lines(names),
            "RESET ALL;",
            "SELECT true AS cleanup_complete;",
        ]
    )
    if table_based:
        lines.append(
            f"DROP TABLE IF EXISTS public.{names['data_table']} CASCADE;"
        )
    return "\n".join(lines).rstrip() + "\n"


def render_alter_aggregate_case(
    plan: StatementRegressPlan,
    case: StatementRegressCase,
) -> str:
    """Render one reviewed ALTER AGGREGATE logical cell."""

    if plan.statement_key != "alter_aggregate" or case not in plan.cases:
        raise RemainingStatementRegressError(
            "ALTER AGGREGATE renderer received a foreign plan or case"
        )
    spec = _spec_for_case(case)
    names = _object_names(case)
    if case.case_group == "system_schema_boundary_product":
        return _render_system_schema_case(plan, case, spec, names)
    return _render_regular_case(plan, case, spec, names)
