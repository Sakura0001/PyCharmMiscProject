-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : DROP AGGREGATE dependency_state=has_dependent_function
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPAGGREGATE00094
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/drop_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/drop_aggregate.yaml
-- primary_obligation_id: DAGG-EXT|00094|drop_aggregate|pg_aggregate_catalog_query|DROP_DEPENDENT_OBJECTS_FIRST
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropaggregate_00094_t CASCADE;
DROP FUNCTION IF EXISTS dropaggregate_00094_depfn CASCADE;
DROP AGGREGATE IF EXISTS dropaggregate_00094_agg(*);
DROP FUNCTION IF EXISTS dropaggregate_00094_sfunc CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地聚合和因子专用夹具。
CREATE FUNCTION dropaggregate_00094_sfunc(int) RETURNS int AS $$ SELECT COALESCE($1, 0) + 1 $$ LANGUAGE SQL;
CREATE AGGREGATE dropaggregate_00094_agg(*) (SFUNC = dropaggregate_00094_sfunc, STYPE = int);
CREATE TABLE dropaggregate_00094_t (c1 int, c2 text);
CREATE FUNCTION dropaggregate_00094_depfn() RETURNS int AS $$ SELECT dropaggregate_00094_agg(*) FROM dropaggregate_00094_t $$ LANGUAGE SQL;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP AGGREGATE。
-- primary-target-begin
DROP AGGREGATE IF EXISTS dropaggregate_00094_agg(*);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS aggregate_present FROM pg_catalog.pg_aggregate a JOIN pg_catalog.pg_proc p ON a.aggfnoid = p.oid WHERE p.proname = 'dropaggregate_00094_agg' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP AGGREGATE IF EXISTS dropaggregate_00094_agg(*) CASCADE;
DROP FUNCTION IF EXISTS dropaggregate_00094_sfunc CASCADE;
DROP FUNCTION IF EXISTS dropaggregate_00094_depfn CASCADE;
DROP TABLE IF EXISTS dropaggregate_00094_t CASCADE;
