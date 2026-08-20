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
-- case_id: CREATEAGGREGATE09118
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/create_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/create_aggregate.yaml
-- primary_obligation_id: CAGG-EXT|09118|pg_proc_query|DROP_AGGREGATE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P17
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP AGGREGATE "createaggregate_09118_Mixed Agg"(boolean);
DROP FUNCTION IF EXISTS createaggregate_09118_nsp.createaggregate_09118_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_09118_ffunc(boolean);
DROP FUNCTION IF EXISTS createaggregate_09118_combine(boolean, boolean);
DROP SCHEMA IF EXISTS createaggregate_09118_nsp CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS createaggregate_09118_nsp;
CREATE FUNCTION createaggregate_09118_nsp.createaggregate_09118_sfunc(text, text) RETURNS boolean AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_09118_ffunc(boolean) RETURNS boolean AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_09118_combine(boolean, boolean) RETURNS boolean AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE AGGREGATE "createaggregate_09118_Mixed Agg" (boolean) (SFUNC = createaggregate_09118_nsp.createaggregate_09118_sfunc, STYPE = boolean, FINALFUNC = createaggregate_09118_ffunc, COMBINEFUNC = createaggregate_09118_combine);
CREATE FUNCTION createaggregate_09118_nsp.createaggregate_09118_sfunc(boolean, text) RETURNS boolean AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE AGGREGATE "createaggregate_09118_Mixed Agg" (text) (SFUNC = createaggregate_09118_nsp.createaggregate_09118_sfunc, STYPE = boolean);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE AGGREGATE。
-- primary-target-begin
CREATE OR REPLACE AGGREGATE "createaggregate_09118_Mixed Agg" (boolean) (SFUNC = createaggregate_09118_nsp.createaggregate_09118_sfunc, STYPE = boolean, FINALFUNC = createaggregate_09118_ffunc, COMBINEFUNC = createaggregate_09118_combine);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42P17' AS target_sqlstate_matches_expected;
SELECT count(*) AS proc_exists FROM pg_catalog.pg_proc WHERE proname = 'createaggregate_09118_Mixed Agg' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP AGGREGATE "createaggregate_09118_Mixed Agg"(boolean);
DROP FUNCTION IF EXISTS createaggregate_09118_nsp.createaggregate_09118_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_09118_ffunc(boolean);
DROP FUNCTION IF EXISTS createaggregate_09118_combine(boolean, boolean);
DROP SCHEMA IF EXISTS createaggregate_09118_nsp CASCADE;
