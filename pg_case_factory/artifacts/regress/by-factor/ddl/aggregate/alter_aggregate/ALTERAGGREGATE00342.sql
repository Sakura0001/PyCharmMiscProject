-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-10
-- version      : 1.0
-- description  : Reject ALTER AGGREGATE RENAME conflict for s01_star_zero_arg
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERAGGREGATE00342
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/alter_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/alter_aggregate.yaml
-- factor_values: statement_branch=branch_rename, aggregate_signature=star_zero_arg, aggregate_form=zero_arg, expected_status=failure, target_state=new_name_conflict, aggregate_name_shape=quoted_identifier, new_name_shape=reserved_word, new_name_conflict=same_signature_conflict, verification_mode=pg_aggregate_catalog_query, cleanup_mode=DROP_AGGREGATE_CASCADE
-- derived_axes: aggregate_kind=n, aggregate_name_shape=quoted_identifier, branch=rename, direct_arg_count=0, expected_sqlstate=42723, failure_cause=same_signature_aggregate_conflict, fixture_kind=zero, flat_arg_count=0, new_name_shape=reserved_word, signature_id=s01_star_zero_arg, signature_key=star_zero_arg, target_signature=*
-- combination_strategy: full conditional Cartesian S14 signatures × 3 aggregate-name shapes × 3 conflicting rename-target shapes
-- session_count: 1
-- execution_profile: same_session_multiphase
-- outer_transaction: forbidden
-- expected_anchor: SQLSTATE 42723 and both original aggregate identities unchanged
-- 1. 幂等清理本编号对象；角色、schema 和关系均只属于当前文件。
RESET ROLE;
RESET SESSION AUTHORIZATION;
SET client_min_messages TO warning;
\set ON_ERROR_STOP on
DROP SCHEMA IF EXISTS alteraggregate_00342_dst CASCADE;
DROP SCHEMA IF EXISTS alteraggregate_00342_src CASCADE;
RESET ROLE;
RESET SESSION AUTHORIZATION;
DROP ROLE IF EXISTS alteraggregate_00342_actor, alteraggregate_00342_intruder, alteraggregate_00342_old_owner, alteraggregate_00342_new_owner;
CREATE SCHEMA alteraggregate_00342_src;
SET search_path TO alteraggregate_00342_src, pg_catalog;

-- 2. 创建完整 support function 与用户自定义聚合；不修改任何内置聚合。
CREATE FUNCTION alteraggregate_00342_src.alteraggregate_00342_step(state bigint) RETURNS bigint
LANGUAGE sql IMMUTABLE
AS 'SELECT state + 1';
CREATE AGGREGATE alteraggregate_00342_src."alteraggregate_00342_Aggregate Name"(*) (
    SFUNC = alteraggregate_00342_src.alteraggregate_00342_step,
    STYPE = bigint,
    INITCOND = '0'
);
SELECT p.oid::text AS before_oid
FROM pg_catalog.pg_proc AS p
JOIN pg_catalog.pg_namespace AS n ON n.oid = p.pronamespace
WHERE n.nspname = 'alteraggregate_00342_src'
  AND p.proname = 'alteraggregate_00342_Aggregate Name'
  AND p.prokind = 'a'
ORDER BY p.oid
\gset

-- 3. 建立本格唯一的目标状态、权限或冲突前置条件。
CREATE AGGREGATE alteraggregate_00342_src."select"(*) (
    SFUNC = alteraggregate_00342_src.alteraggregate_00342_step,
    STYPE = bigint,
    INITCOND = '0'
);
SELECT true AS target_context_ready;

-- 4. 执行唯一目标 ALTER AGGREGATE；expected SQLSTATE 42723。
\set ON_ERROR_STOP off
ALTER AGGREGATE "alteraggregate_00342_Aggregate Name"(*) RENAME TO "select";
\echo target_sqlstate :SQLSTATE
SELECT :'SQLSTATE' = '42723' AS target_sqlstate_matches;
\set ON_ERROR_STOP on
RESET ROLE;

-- 5. 用 schema、prokind、aggkind、direct 参数数、arity 和保存的 OID 验证结果。
SELECT
    count(*) = 1 AS target_aggregate_present,
    COALESCE(bool_and(p.oid::text = :'before_oid'), false) AS target_aggregate_oid_stable,
    COALESCE(bool_and(a.aggkind = 'n'), false) AS target_aggregate_kind_stable,
    COALESCE(bool_and(a.aggnumdirectargs = 0), false) AS target_aggregate_direct_count_stable,
    COALESCE(bool_and(p.pronargs = 0), false) AS target_aggregate_arity_stable
FROM pg_catalog.pg_proc AS p
JOIN pg_catalog.pg_namespace AS n ON n.oid = p.pronamespace
JOIN pg_catalog.pg_aggregate AS a ON a.aggfnoid = p.oid
WHERE n.nspname = 'alteraggregate_00342_src'
  AND p.proname = 'alteraggregate_00342_Aggregate Name'
  AND p.prokind = 'a'
ORDER BY target_aggregate_present, target_aggregate_oid_stable, target_aggregate_kind_stable, target_aggregate_direct_count_stable, target_aggregate_arity_stable;

-- 6. 成功主积执行修改后的聚合；失败格只做独立会话可用性和不变性锚定。
SELECT true AS session_usable_after_target;

-- 7. 按实际最终 identity 反向清理 aggregate、support functions、schema、role 与输入表。
RESET ROLE;
RESET SESSION AUTHORIZATION;
DROP AGGREGATE IF EXISTS alteraggregate_00342_src."select"(*) CASCADE;
DROP AGGREGATE IF EXISTS alteraggregate_00342_dst."alteraggregate_00342_Aggregate Name"(*) CASCADE;
DROP AGGREGATE IF EXISTS alteraggregate_00342_src."alteraggregate_00342_Aggregate Name"(*) CASCADE;
DROP SCHEMA IF EXISTS alteraggregate_00342_dst CASCADE;
DROP SCHEMA IF EXISTS alteraggregate_00342_src CASCADE;
RESET ROLE;
RESET SESSION AUTHORIZATION;
DROP ROLE IF EXISTS alteraggregate_00342_actor, alteraggregate_00342_intruder, alteraggregate_00342_old_owner, alteraggregate_00342_new_owner;
RESET ALL;
SELECT true AS cleanup_complete;
