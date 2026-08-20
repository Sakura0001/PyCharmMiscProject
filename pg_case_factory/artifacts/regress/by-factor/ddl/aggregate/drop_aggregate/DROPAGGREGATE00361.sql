-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : DROP AGGREGATE privilege_level=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPAGGREGATE00361
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/drop_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/drop_aggregate.yaml
-- primary_obligation_id: DAGG-EXT|00361|drop_aggregate|pg_aggregate_catalog_query|DROP_AGGREGATE_CASCADE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP AGGREGATE IF EXISTS dropaggregate_00361_schema.dropaggregate_00361_agg(*) CASCADE;
DROP FUNCTION IF EXISTS dropaggregate_00361_sfunc CASCADE;
DROP SCHEMA IF EXISTS dropaggregate_00361_schema CASCADE;
DROP ROLE IF EXISTS dropaggregate_00361_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地聚合和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS dropaggregate_00361_schema;
CREATE ROLE dropaggregate_00361_actor LOGIN NOSUPERUSER;
GRANT USAGE ON SCHEMA dropaggregate_00361_schema TO dropaggregate_00361_actor;
CREATE FUNCTION dropaggregate_00361_sfunc(int) RETURNS int AS $$ SELECT COALESCE($1, 0) + 1 $$ LANGUAGE SQL;
CREATE AGGREGATE dropaggregate_00361_schema.dropaggregate_00361_agg(*) (SFUNC = dropaggregate_00361_sfunc, STYPE = int);
SET ROLE dropaggregate_00361_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP AGGREGATE。
-- primary-target-begin
DROP AGGREGATE dropaggregate_00361_schema.dropaggregate_00361_agg(*) RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS aggregate_present FROM pg_catalog.pg_aggregate a JOIN pg_catalog.pg_proc p ON a.aggfnoid = p.oid WHERE p.proname = 'dropaggregate_00361_agg' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP AGGREGATE IF EXISTS dropaggregate_00361_schema.dropaggregate_00361_agg(*) CASCADE;
DROP FUNCTION IF EXISTS dropaggregate_00361_sfunc CASCADE;
DROP SCHEMA IF EXISTS dropaggregate_00361_schema CASCADE;
DROP OWNED BY dropaggregate_00361_actor;
DROP ROLE IF EXISTS dropaggregate_00361_actor;
