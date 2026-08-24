-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-10
-- version      : 1.0
-- description  : Reject ALTER AGGREGATE rename for isolated aggregate_not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERAGGREGATE00673
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/alter_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/alter_aggregate.yaml
-- factor_values: statement_branch=branch_rename, aggregate_signature=single_argtype, aggregate_form=single_arg, expected_status=failure, aggregate_not_exists=not_exists, verification_mode=pg_aggregate_catalog_query, cleanup_mode=DROP_AGGREGATE_IF_EXISTS
-- derived_axes: aggregate_kind=n, aggregate_name_shape=schema_qualified, branch=rename, direct_arg_count=0, expected_sqlstate=42883, fixture_kind=single, flat_arg_count=1, lookup_failure=aggregate_not_exists, signature_id=s02_single_arg, signature_key=single_argtype, target_signature=integer
-- combination_strategy: full Cartesian 3 action branches × 4 isolated aggregate lookup failures
-- session_count: 1
-- execution_profile: same_session_multiphase
-- outer_transaction: forbidden
-- expected_anchor: SQLSTATE 42883 and any existing control aggregate unchanged
-- 1. 幂等清理本编号对象；角色、schema 和关系均只属于当前文件。
RESET ROLE;
RESET SESSION AUTHORIZATION;
SET client_min_messages TO warning;
\set ON_ERROR_STOP on
DROP SCHEMA IF EXISTS alteraggregate_00673_dst CASCADE;
DROP SCHEMA IF EXISTS alteraggregate_00673_src CASCADE;
RESET ROLE;
RESET SESSION AUTHORIZATION;
DROP ROLE IF EXISTS alteraggregate_00673_actor, alteraggregate_00673_intruder, alteraggregate_00673_old_owner, alteraggregate_00673_new_owner;
CREATE SCHEMA alteraggregate_00673_src;
SET search_path TO alteraggregate_00673_src, pg_catalog;

-- 2. 创建完整 support function 与用户自定义聚合；不修改任何内置聚合。
SELECT true AS no_aggregate_fixture_required;

-- 3. 建立本格唯一的目标状态、权限或冲突前置条件。
SELECT true AS target_context_ready;

-- 4. 执行唯一目标 ALTER AGGREGATE；expected SQLSTATE 42883。
\set ON_ERROR_STOP off
ALTER AGGREGATE alteraggregate_00673_src."alteraggregate_00673_missing_aggregate"(integer) RENAME TO alteraggregate_00673_renamed;
\echo target_sqlstate :SQLSTATE
SELECT :'SQLSTATE' = '42883' AS target_sqlstate_matches;
\set ON_ERROR_STOP on
RESET ROLE;

-- 5. 用 schema、prokind、aggkind、direct 参数数、arity 和保存的 OID 验证结果。
SELECT count(*) = 0 AS aggregate_remains_absent
FROM pg_catalog.pg_proc AS p
JOIN pg_catalog.pg_namespace AS n ON n.oid = p.pronamespace
WHERE n.nspname = 'alteraggregate_00673_src'
  AND p.proname = 'alteraggregate_00673_missing_aggregate'
  AND p.prokind = 'a'
ORDER BY aggregate_remains_absent;

-- 6. 成功主积执行修改后的聚合；失败格只做独立会话可用性和不变性锚定。
SELECT true AS session_usable_after_target;

-- 7. 按实际最终 identity 反向清理 aggregate、support functions、schema、role 与输入表。
RESET ROLE;
RESET SESSION AUTHORIZATION;
DROP AGGREGATE IF EXISTS alteraggregate_00673_src.alteraggregate_00673_renamed(original_value integer) CASCADE;
DROP AGGREGATE IF EXISTS alteraggregate_00673_dst."alteraggregate_00673_agg"(original_value integer) CASCADE;
DROP AGGREGATE IF EXISTS alteraggregate_00673_src."alteraggregate_00673_missing_aggregate"(original_value integer) CASCADE;
DROP SCHEMA IF EXISTS alteraggregate_00673_dst CASCADE;
DROP SCHEMA IF EXISTS alteraggregate_00673_src CASCADE;
RESET ROLE;
RESET SESSION AUTHORIZATION;
DROP ROLE IF EXISTS alteraggregate_00673_actor, alteraggregate_00673_intruder, alteraggregate_00673_old_owner, alteraggregate_00673_new_owner;
RESET ALL;
SELECT true AS cleanup_complete;
