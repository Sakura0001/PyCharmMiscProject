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
-- case_id: DROPAGGREGATE00239
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/drop_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/drop_aggregate.yaml
-- primary_obligation_id: DAGG-EXT|00239|drop_aggregate|pg_aggregate_removed_assertion|DROP_AGGREGATE_CASCADE
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropaggregate_00239_t CASCADE;
DROP FUNCTION IF EXISTS dropaggregate_00239_depfn CASCADE;
DROP AGGREGATE IF EXISTS "dropaggregate_00239_QuotedAgg"(*) CASCADE;
DROP FUNCTION IF EXISTS dropaggregate_00239_sfunc CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地聚合和因子专用夹具。
CREATE FUNCTION dropaggregate_00239_sfunc(int) RETURNS int AS $$ SELECT COALESCE($1, 0) + 1 $$ LANGUAGE SQL;
CREATE AGGREGATE "dropaggregate_00239_QuotedAgg"(*) (SFUNC = dropaggregate_00239_sfunc, STYPE = int);
CREATE TABLE dropaggregate_00239_t (c1 int, c2 text);
CREATE FUNCTION dropaggregate_00239_depfn() RETURNS int AS $$ SELECT "dropaggregate_00239_QuotedAgg"(*) FROM dropaggregate_00239_t $$ LANGUAGE SQL;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP AGGREGATE。
-- primary-target-begin
DROP AGGREGATE IF EXISTS "dropaggregate_00239_QuotedAgg"(*) RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS aggregate_present FROM pg_catalog.pg_aggregate a JOIN pg_catalog.pg_proc p ON a.aggfnoid = p.oid WHERE p.proname = 'dropaggregate_00239_QuotedAgg' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP AGGREGATE IF EXISTS "dropaggregate_00239_QuotedAgg"(*) CASCADE;
DROP FUNCTION IF EXISTS dropaggregate_00239_sfunc CASCADE;
DROP FUNCTION IF EXISTS dropaggregate_00239_depfn CASCADE;
DROP TABLE IF EXISTS dropaggregate_00239_t CASCADE;
