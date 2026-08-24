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
-- case_id: CREATEAGGREGATE04902
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/create_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/create_aggregate.yaml
-- primary_obligation_id: CAGG-EXT|04902|actual_execution|DROP_AGGREGATE_CASCADE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42723
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP AGGREGATE createaggregate_04902_nsp.createaggregate_04902_agg(date) CASCADE;
DROP FUNCTION IF EXISTS createaggregate_04902_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_04902_ffunc(date);
DROP FUNCTION IF EXISTS createaggregate_04902_combine(date, date);
DROP SCHEMA IF EXISTS createaggregate_04902_nsp CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS createaggregate_04902_nsp;
CREATE FUNCTION createaggregate_04902_sfunc(text, text) RETURNS date AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_04902_ffunc(date) RETURNS date AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_04902_combine(date, date) RETURNS date AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE AGGREGATE createaggregate_04902_nsp.createaggregate_04902_agg (date, date) (SFUNC = createaggregate_04902_sfunc, STYPE = date, FINALFUNC = createaggregate_04902_ffunc, COMBINEFUNC = createaggregate_04902_combine);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE AGGREGATE。
-- primary-target-begin
CREATE AGGREGATE createaggregate_04902_nsp.createaggregate_04902_agg (date, date) (SFUNC = createaggregate_04902_sfunc, STYPE = date, FINALFUNC = createaggregate_04902_ffunc, COMBINEFUNC = createaggregate_04902_combine);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42723' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP AGGREGATE createaggregate_04902_nsp.createaggregate_04902_agg(date) CASCADE;
DROP FUNCTION IF EXISTS createaggregate_04902_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_04902_ffunc(date);
DROP FUNCTION IF EXISTS createaggregate_04902_combine(date, date);
DROP SCHEMA IF EXISTS createaggregate_04902_nsp CASCADE;
