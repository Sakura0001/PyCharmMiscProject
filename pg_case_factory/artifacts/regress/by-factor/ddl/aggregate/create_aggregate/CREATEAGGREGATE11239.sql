-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE AGGREGATE object_state=already_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEAGGREGATE11239
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/create_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/create_aggregate.yaml
-- primary_obligation_id: CAGG-EXT|11239|pg_aggregate_catalog_query|DROP_AGGREGATE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42723
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP AGGREGATE "order"(numeric);
DROP FUNCTION IF EXISTS createaggregate_11239_nsp.createaggregate_11239_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_11239_ffunc(numeric);
DROP FUNCTION IF EXISTS createaggregate_11239_combine(numeric, numeric);
DROP SCHEMA IF EXISTS createaggregate_11239_nsp CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS createaggregate_11239_nsp;
CREATE FUNCTION createaggregate_11239_nsp.createaggregate_11239_sfunc(text, text) RETURNS numeric AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_11239_ffunc(numeric) RETURNS numeric AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_11239_combine(numeric, numeric) RETURNS numeric AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE AGGREGATE "order" (numeric) (SFUNC = createaggregate_11239_nsp.createaggregate_11239_sfunc, STYPE = numeric, FINALFUNC = createaggregate_11239_ffunc, COMBINEFUNC = createaggregate_11239_combine);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE AGGREGATE。
-- primary-target-begin
CREATE AGGREGATE "order" (numeric) (SFUNC = createaggregate_11239_nsp.createaggregate_11239_sfunc, STYPE = numeric, FINALFUNC = createaggregate_11239_ffunc, COMBINEFUNC = createaggregate_11239_combine);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42723' AS target_sqlstate_matches_expected;
SELECT count(*) AS agg_exists FROM pg_catalog.pg_aggregate a JOIN pg_catalog.pg_proc p ON a.aggfnoid = p.oid WHERE p.proname = 'order' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP AGGREGATE "order"(numeric);
DROP FUNCTION IF EXISTS createaggregate_11239_nsp.createaggregate_11239_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_11239_ffunc(numeric);
DROP FUNCTION IF EXISTS createaggregate_11239_combine(numeric, numeric);
DROP SCHEMA IF EXISTS createaggregate_11239_nsp CASCADE;
