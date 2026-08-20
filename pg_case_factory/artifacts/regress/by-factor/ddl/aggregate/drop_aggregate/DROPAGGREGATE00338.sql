-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : DROP AGGREGATE object_state=already_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPAGGREGATE00338
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/drop_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/drop_aggregate.yaml
-- primary_obligation_id: DAGG-EXT|00338|drop_aggregate|pg_aggregate_catalog_query|DROP_DEPENDENT_OBJECTS_FIRST
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP AGGREGATE IF EXISTS dropaggregate_00338_schema.dropaggregate_00338_agg(*);
DROP FUNCTION IF EXISTS dropaggregate_00338_sfunc CASCADE;
DROP SCHEMA IF EXISTS dropaggregate_00338_schema CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地聚合和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS dropaggregate_00338_schema;
CREATE FUNCTION dropaggregate_00338_sfunc(int) RETURNS int AS $$ SELECT COALESCE($1, 0) + 1 $$ LANGUAGE SQL;
CREATE AGGREGATE dropaggregate_00338_schema.dropaggregate_00338_agg(*) (SFUNC = dropaggregate_00338_sfunc, STYPE = int);
-- 3. 执行唯一获得覆盖信用的 DROP AGGREGATE。
-- primary-target-begin
DROP AGGREGATE dropaggregate_00338_schema.dropaggregate_00338_agg(*);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS aggregate_absent FROM pg_catalog.pg_aggregate a JOIN pg_catalog.pg_proc p ON a.aggfnoid = p.oid WHERE p.proname = 'dropaggregate_00338_agg' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP AGGREGATE IF EXISTS dropaggregate_00338_schema.dropaggregate_00338_agg(*) CASCADE;
DROP FUNCTION IF EXISTS dropaggregate_00338_sfunc CASCADE;
DROP SCHEMA IF EXISTS dropaggregate_00338_schema CASCADE;
