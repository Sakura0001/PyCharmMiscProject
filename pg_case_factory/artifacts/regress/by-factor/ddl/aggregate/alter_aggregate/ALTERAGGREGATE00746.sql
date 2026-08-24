-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-10
-- version      : 1.0
-- description  : Reject ALTER AGGREGATE move_into pg_temp
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERAGGREGATE00746
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/alter_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/alter_aggregate.yaml
-- factor_values: statement_branch=branch_set_schema, aggregate_signature=single_argtype, aggregate_form=single_arg, expected_status=failure, verification_mode=pg_aggregate_catalog_query, cleanup_mode=DROP_AGGREGATE_CASCADE
-- derived_axes: aggregate_kind=n, aggregate_name_shape=schema_qualified, branch=set_schema, direct_arg_count=0, direction=move_into, expected_sqlstate=0A000, fixture_kind=single, flat_arg_count=1, signature_id=s02_single_arg, signature_key=single_argtype, system_schema=pg_temp, target_signature=integer
-- combination_strategy: full Cartesian {pg_temp, pg_toast} × {move into, move out}
-- session_count: 1
-- execution_profile: external_isolated
-- outer_transaction: forbidden
-- expected_anchor: SQLSTATE 0A000 and no system-schema object leakage
-- 1. 清理本编号普通 schema、角色和可能残留的系统 schema 测试对象。
RESET ROLE;
RESET SESSION AUTHORIZATION;
SET client_min_messages TO warning;
\set ON_ERROR_STOP on
DROP SCHEMA IF EXISTS alteraggregate_00746_dst CASCADE;
DROP SCHEMA IF EXISTS alteraggregate_00746_src CASCADE;
CREATE TEMP SEQUENCE IF NOT EXISTS alteraggregate_00746_temp_sequence;
DROP AGGREGATE IF EXISTS pg_temp."alteraggregate_00746_agg"(integer) CASCADE;
DROP FUNCTION IF EXISTS pg_temp.alteraggregate_00746_step(bigint, integer) CASCADE;

-- 2. 在移动源 schema 建立完整 support function 与单参数聚合 fixture。
CREATE SCHEMA alteraggregate_00746_src;
CREATE FUNCTION alteraggregate_00746_src.alteraggregate_00746_step(state bigint, value integer) RETURNS bigint
LANGUAGE sql IMMUTABLE
AS 'SELECT state + COALESCE(value, 0)';
CREATE AGGREGATE alteraggregate_00746_src."alteraggregate_00746_agg"(original_value integer) (
    SFUNC = alteraggregate_00746_src.alteraggregate_00746_step,
    STYPE = bigint,
    INITCOND = '0'
);

-- 3. 保存源对象 OID，仅在后续布尔比较中使用，避免输出不稳定标识。
SELECT p.oid::text AS before_oid
FROM pg_catalog.pg_proc AS p
JOIN pg_catalog.pg_namespace AS n ON n.oid = p.pronamespace
WHERE n.nspname = 'alteraggregate_00746_src'
  AND p.proname = 'alteraggregate_00746_agg'
  AND p.prokind = 'a'
ORDER BY p.oid
\gset

-- 4. 执行唯一目标 SET SCHEMA pg_temp；expected SQLSTATE 0A000。
\set ON_ERROR_STOP off
ALTER AGGREGATE alteraggregate_00746_src."alteraggregate_00746_agg"(integer) SET SCHEMA pg_temp;
\echo target_sqlstate :SQLSTATE
SELECT :'SQLSTATE' = '0A000' AS target_sqlstate_matches;
\set ON_ERROR_STOP on

-- 5. 确认失败后源聚合仍在原 namespace，且 OID、kind、arity 均未改变。
SELECT
    count(*) = 1 AS source_aggregate_present,
    COALESCE(bool_and(p.oid::text = :'before_oid'), false) AS source_aggregate_oid_stable,
    COALESCE(bool_and(a.aggkind = 'n'), false) AS source_aggregate_kind_stable,
    COALESCE(bool_and(a.aggnumdirectargs = 0), false) AS source_aggregate_direct_count_stable,
    COALESCE(bool_and(p.pronargs = 1), false) AS source_aggregate_arity_stable
FROM pg_catalog.pg_proc AS p
JOIN pg_catalog.pg_namespace AS n ON n.oid = p.pronamespace
JOIN pg_catalog.pg_aggregate AS a ON a.aggfnoid = p.oid
WHERE n.nspname = 'alteraggregate_00746_src'
  AND p.proname = 'alteraggregate_00746_agg'
  AND p.prokind = 'a'
ORDER BY source_aggregate_present, source_aggregate_oid_stable, source_aggregate_kind_stable, source_aggregate_direct_count_stable, source_aggregate_arity_stable;

-- 6. 显式删除系统 schema 中的编号对象，避免污染后续文件。
DROP AGGREGATE IF EXISTS alteraggregate_00746_src."alteraggregate_00746_agg"(integer) CASCADE;
DROP FUNCTION IF EXISTS alteraggregate_00746_src.alteraggregate_00746_step(bigint, integer) CASCADE;

-- 7. 反向清理普通 schema 与临时序列，并给出稳定完成锚点。
DROP SCHEMA IF EXISTS alteraggregate_00746_dst CASCADE;
DROP SCHEMA IF EXISTS alteraggregate_00746_src CASCADE;
DROP SEQUENCE IF EXISTS pg_temp.alteraggregate_00746_temp_sequence;
RESET ALL;
SELECT true AS cleanup_complete;
