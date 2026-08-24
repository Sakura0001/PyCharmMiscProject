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
-- case_id: DROPAGGREGATE00268
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/drop_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/drop_aggregate.yaml
-- primary_obligation_id: DAGG-EXT|00268|drop_aggregate|pg_aggregate_removed_assertion|DROP_DEPENDENT_OBJECTS_FIRST
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropaggregate_00268_t CASCADE;
DROP FUNCTION IF EXISTS dropaggregate_00268_depfn CASCADE;
DROP AGGREGATE IF EXISTS dropaggregate_00268_schema.dropaggregate_00268_agg(*);
DROP FUNCTION IF EXISTS dropaggregate_00268_sfunc CASCADE;
DROP SCHEMA IF EXISTS dropaggregate_00268_schema CASCADE;
DROP ROLE IF EXISTS dropaggregate_00268_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地聚合和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS dropaggregate_00268_schema;
CREATE ROLE dropaggregate_00268_actor LOGIN NOSUPERUSER;
GRANT USAGE ON SCHEMA dropaggregate_00268_schema TO dropaggregate_00268_actor;
CREATE FUNCTION dropaggregate_00268_sfunc(int) RETURNS int AS $$ SELECT COALESCE($1, 0) + 1 $$ LANGUAGE SQL;
CREATE AGGREGATE dropaggregate_00268_schema.dropaggregate_00268_agg(*) (SFUNC = dropaggregate_00268_sfunc, STYPE = int);
CREATE TABLE dropaggregate_00268_t (c1 int, c2 text);
CREATE FUNCTION dropaggregate_00268_depfn() RETURNS int AS $$ SELECT dropaggregate_00268_schema.dropaggregate_00268_agg(*) FROM dropaggregate_00268_t $$ LANGUAGE SQL;
SET ROLE dropaggregate_00268_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP AGGREGATE。
-- primary-target-begin
DROP AGGREGATE dropaggregate_00268_schema.dropaggregate_00268_agg(*) CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS aggregate_present FROM pg_catalog.pg_aggregate a JOIN pg_catalog.pg_proc p ON a.aggfnoid = p.oid WHERE p.proname = 'dropaggregate_00268_agg' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP AGGREGATE IF EXISTS dropaggregate_00268_schema.dropaggregate_00268_agg(*) CASCADE;
DROP FUNCTION IF EXISTS dropaggregate_00268_sfunc CASCADE;
DROP FUNCTION IF EXISTS dropaggregate_00268_depfn CASCADE;
DROP SCHEMA IF EXISTS dropaggregate_00268_schema CASCADE;
DROP OWNED BY dropaggregate_00268_actor;
DROP ROLE IF EXISTS dropaggregate_00268_actor;
DROP TABLE IF EXISTS dropaggregate_00268_t CASCADE;
