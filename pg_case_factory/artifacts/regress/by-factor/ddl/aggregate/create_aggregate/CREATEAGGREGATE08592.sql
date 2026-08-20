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
-- case_id: CREATEAGGREGATE08592
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/create_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/create_aggregate.yaml
-- primary_obligation_id: CAGG-EXT|08592|actual_execution|DROP_AGGREGATE_CASCADE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P17
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP AGGREGATE createaggregate_08592_agg(timestamp) CASCADE;
DROP FUNCTION IF EXISTS createaggregate_08592_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_08592_ffunc(timestamp);
DROP FUNCTION IF EXISTS createaggregate_08592_combine(timestamp, timestamp);
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FUNCTION createaggregate_08592_sfunc(text, text) RETURNS timestamp AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_08592_ffunc(timestamp) RETURNS timestamp AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_08592_combine(timestamp, timestamp) RETURNS timestamp AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE AGGREGATE createaggregate_08592_agg (BASETYPE = timestamp) (BASETYPE = timestamp, SFUNC = createaggregate_08592_sfunc, STYPE = timestamp, FINALFUNC = createaggregate_08592_ffunc, COMBINEFUNC = createaggregate_08592_combine);
CREATE FUNCTION createaggregate_08592_sfunc(timestamp, text) RETURNS timestamp AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE AGGREGATE createaggregate_08592_agg (text) (SFUNC = createaggregate_08592_sfunc, STYPE = timestamp);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE AGGREGATE。
-- primary-target-begin
CREATE OR REPLACE AGGREGATE createaggregate_08592_agg (BASETYPE = timestamp) (BASETYPE = timestamp, SFUNC = createaggregate_08592_sfunc, STYPE = timestamp, FINALFUNC = createaggregate_08592_ffunc, COMBINEFUNC = createaggregate_08592_combine);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42P17' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP AGGREGATE createaggregate_08592_agg(timestamp) CASCADE;
DROP FUNCTION IF EXISTS createaggregate_08592_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_08592_ffunc(timestamp);
DROP FUNCTION IF EXISTS createaggregate_08592_combine(timestamp, timestamp);
