-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : DROP AGGREGATE dependent_objects_exist=restrict_with_dependencies
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPAGGREGATE00017
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/drop_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/drop_aggregate.yaml
-- primary_obligation_id: DAGG-SFV|sfv-fc9e4a020f68ea5aa57d36e7|drop_aggregate
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropaggregate_00017_t CASCADE;
DROP VIEW IF EXISTS dropaggregate_00017_depv CASCADE;
DROP AGGREGATE IF EXISTS dropaggregate_00017_agg(*) CASCADE;
DROP FUNCTION IF EXISTS dropaggregate_00017_sfunc CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地聚合和因子专用夹具。
CREATE FUNCTION dropaggregate_00017_sfunc(int) RETURNS int AS $$ SELECT COALESCE($1, 0) + 1 $$ LANGUAGE SQL;
CREATE AGGREGATE dropaggregate_00017_agg(*) (SFUNC = dropaggregate_00017_sfunc, STYPE = int);
CREATE TABLE dropaggregate_00017_t (c1 int, c2 text);
CREATE VIEW dropaggregate_00017_depv AS SELECT dropaggregate_00017_agg(*) FROM dropaggregate_00017_t;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP AGGREGATE。
-- primary-target-begin
DROP AGGREGATE dropaggregate_00017_agg(*);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS aggregate_present FROM pg_catalog.pg_aggregate a JOIN pg_catalog.pg_proc p ON a.aggfnoid = p.oid WHERE p.proname = 'dropaggregate_00017_agg' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP AGGREGATE IF EXISTS dropaggregate_00017_agg(*) CASCADE;
DROP FUNCTION IF EXISTS dropaggregate_00017_sfunc CASCADE;
DROP VIEW IF EXISTS dropaggregate_00017_depv CASCADE;
DROP TABLE IF EXISTS dropaggregate_00017_t CASCADE;
