-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-10
-- version      : 1.0
-- description  : Verify OWNER TO same owner no-op for aggregate_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERAGGREGATE00716
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/alter_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/alter_aggregate.yaml
-- factor_values: statement_branch=branch_owner, aggregate_signature=single_argtype, aggregate_form=single_arg, expected_status=success, target_state=new_owner_available, new_owner_shape=plain_role, privilege_level=aggregate_owner, verification_mode=pg_proc_query, cleanup_mode=DROP_AGGREGATE_IF_EXISTS
-- derived_axes: aggregate_kind=n, aggregate_name_shape=schema_qualified, branch=owner, direct_arg_count=0, expected_sqlstate=00000, fixture_kind=single, flat_arg_count=1, owner_shape=plain_role, privilege=aggregate_owner, same_owner=yes, signature_id=s02_single_arg, signature_key=single_argtype, target_signature=integer
-- combination_strategy: full privilege-level product for OWNER TO existing owner early no-op
-- session_count: 1
-- execution_profile: same_session_multiphase
-- outer_transaction: forbidden
-- expected_anchor: SQLSTATE 00000 and proowner unchanged even for the non-owner early-return cell
-- 1. 幂等清理本编号对象；角色、schema 和关系均只属于当前文件。
RESET ROLE;
RESET SESSION AUTHORIZATION;
SET client_min_messages TO warning;
\set ON_ERROR_STOP on
DROP SCHEMA IF EXISTS alteraggregate_00716_dst CASCADE;
DROP SCHEMA IF EXISTS alteraggregate_00716_src CASCADE;
RESET ROLE;
RESET SESSION AUTHORIZATION;
DROP ROLE IF EXISTS alteraggregate_00716_actor, alteraggregate_00716_intruder, alteraggregate_00716_old_owner, alteraggregate_00716_new_owner;
CREATE SCHEMA alteraggregate_00716_src;
SET search_path TO alteraggregate_00716_src, pg_catalog;

-- 2. 创建完整 support function 与用户自定义聚合；不修改任何内置聚合。
CREATE FUNCTION alteraggregate_00716_src.alteraggregate_00716_step(state bigint, value integer) RETURNS bigint
LANGUAGE sql IMMUTABLE
AS 'SELECT state + COALESCE(value, 0)';
CREATE AGGREGATE alteraggregate_00716_src."alteraggregate_00716_agg"(original_value integer) (
    SFUNC = alteraggregate_00716_src.alteraggregate_00716_step,
    STYPE = bigint,
    INITCOND = '0'
);
SELECT p.oid::text AS before_oid
FROM pg_catalog.pg_proc AS p
JOIN pg_catalog.pg_namespace AS n ON n.oid = p.pronamespace
WHERE n.nspname = 'alteraggregate_00716_src'
  AND p.proname = 'alteraggregate_00716_agg'
  AND p.prokind = 'a'
ORDER BY p.oid
\gset

-- 3. 建立本格唯一的目标状态、权限或冲突前置条件。
CREATE ROLE alteraggregate_00716_old_owner NOLOGIN;
CREATE ROLE alteraggregate_00716_intruder NOLOGIN;
GRANT USAGE ON SCHEMA alteraggregate_00716_src TO alteraggregate_00716_old_owner;
GRANT USAGE ON SCHEMA alteraggregate_00716_src TO alteraggregate_00716_intruder;
ALTER ROUTINE alteraggregate_00716_src."alteraggregate_00716_agg"(integer) OWNER TO alteraggregate_00716_old_owner;
SET ROLE alteraggregate_00716_old_owner;
SELECT true AS target_context_ready;

-- 4. 执行唯一目标 ALTER AGGREGATE；expected SQLSTATE 00000。
\set ON_ERROR_STOP off
ALTER AGGREGATE alteraggregate_00716_src."alteraggregate_00716_agg"(integer) OWNER TO alteraggregate_00716_old_owner;
\echo target_sqlstate :SQLSTATE
SELECT :'SQLSTATE' = '00000' AS target_sqlstate_matches;
\set ON_ERROR_STOP on
RESET ROLE;

-- 5. 用 schema、prokind、aggkind、direct 参数数、arity 和保存的 OID 验证结果。
SELECT
    count(*) = 1 AS target_aggregate_present,
    COALESCE(bool_and(p.oid::text = :'before_oid'), false) AS target_aggregate_oid_stable,
    COALESCE(bool_and(a.aggkind = 'n'), false) AS target_aggregate_kind_stable,
    COALESCE(bool_and(a.aggnumdirectargs = 0), false) AS target_aggregate_direct_count_stable,
    COALESCE(bool_and(p.pronargs = 1), false) AS target_aggregate_arity_stable
FROM pg_catalog.pg_proc AS p
JOIN pg_catalog.pg_namespace AS n ON n.oid = p.pronamespace
JOIN pg_catalog.pg_aggregate AS a ON a.aggfnoid = p.oid
WHERE n.nspname = 'alteraggregate_00716_src'
  AND p.proname = 'alteraggregate_00716_agg'
  AND p.prokind = 'a'
ORDER BY target_aggregate_present, target_aggregate_oid_stable, target_aggregate_kind_stable, target_aggregate_direct_count_stable, target_aggregate_arity_stable;
SELECT count(*) = 1 AS owner_matches
FROM pg_catalog.pg_proc AS p
JOIN pg_catalog.pg_namespace AS n ON n.oid = p.pronamespace
WHERE n.nspname = 'alteraggregate_00716_src'
  AND p.proname = 'alteraggregate_00716_agg'
  AND p.prokind = 'a'
  AND pg_catalog.pg_get_userbyid(p.proowner) = 'alteraggregate_00716_old_owner'
ORDER BY owner_matches;

-- 6. 成功主积执行修改后的聚合；失败格只做独立会话可用性和不变性锚定。
SELECT true AS session_usable_after_target;

-- 7. 按实际最终 identity 反向清理 aggregate、support functions、schema、role 与输入表。
RESET ROLE;
RESET SESSION AUTHORIZATION;
DROP AGGREGATE IF EXISTS alteraggregate_00716_src.alteraggregate_00716_renamed(original_value integer) CASCADE;
DROP AGGREGATE IF EXISTS alteraggregate_00716_dst."alteraggregate_00716_agg"(original_value integer) CASCADE;
DROP AGGREGATE IF EXISTS alteraggregate_00716_src."alteraggregate_00716_agg"(original_value integer) CASCADE;
DROP SCHEMA IF EXISTS alteraggregate_00716_dst CASCADE;
DROP SCHEMA IF EXISTS alteraggregate_00716_src CASCADE;
RESET ROLE;
RESET SESSION AUTHORIZATION;
DROP ROLE IF EXISTS alteraggregate_00716_actor, alteraggregate_00716_intruder, alteraggregate_00716_old_owner, alteraggregate_00716_old_owner;
RESET ALL;
SELECT true AS cleanup_complete;
