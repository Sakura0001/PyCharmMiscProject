-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE AGGREGATE or_replace_clause=present_replace_with_constraint_violation
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEAGGREGATE15167
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/create_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/create_aggregate.yaml
-- primary_obligation_id: CAGG-EXT|15167|pg_proc_query|DROP_AGGREGATE_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P17
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP AGGREGATE IF EXISTS "createaggregate_15167_Mixed Agg";
DROP FUNCTION IF EXISTS createaggregate_15167_nsp.createaggregate_15167_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_15167_ffunc(float8);
DROP FUNCTION IF EXISTS createaggregate_15167_combine(float8, float8);
DROP SCHEMA IF EXISTS createaggregate_15167_nsp CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS createaggregate_15167_nsp;
CREATE FUNCTION createaggregate_15167_nsp.createaggregate_15167_sfunc(text, text) RETURNS float8 AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_15167_ffunc(float8) RETURNS float8 AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_15167_combine(float8, float8) RETURNS float8 AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE AGGREGATE "createaggregate_15167_Mixed Agg" () (SFUNC = createaggregate_15167_nsp.createaggregate_15167_sfunc, STYPE = float8, FINALFUNC = createaggregate_15167_ffunc, COMBINEFUNC = createaggregate_15167_combine);
CREATE FUNCTION createaggregate_15167_nsp.createaggregate_15167_sfunc(float8, text) RETURNS float8 AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE AGGREGATE "createaggregate_15167_Mixed Agg" (text) (SFUNC = createaggregate_15167_nsp.createaggregate_15167_sfunc, STYPE = float8);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE AGGREGATE。
-- primary-target-begin
CREATE OR REPLACE AGGREGATE "createaggregate_15167_Mixed Agg" () (SFUNC = createaggregate_15167_nsp.createaggregate_15167_sfunc, STYPE = float8, FINALFUNC = createaggregate_15167_ffunc, COMBINEFUNC = createaggregate_15167_combine);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42P17' AS target_sqlstate_matches_expected;
SELECT count(*) AS proc_exists FROM pg_catalog.pg_proc WHERE proname = 'createaggregate_15167_Mixed Agg' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP AGGREGATE IF EXISTS "createaggregate_15167_Mixed Agg";
DROP FUNCTION IF EXISTS createaggregate_15167_nsp.createaggregate_15167_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_15167_ffunc(float8);
DROP FUNCTION IF EXISTS createaggregate_15167_combine(float8, float8);
DROP SCHEMA IF EXISTS createaggregate_15167_nsp CASCADE;
