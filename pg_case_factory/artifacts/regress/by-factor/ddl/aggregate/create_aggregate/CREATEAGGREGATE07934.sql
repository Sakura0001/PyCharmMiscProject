-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE AGGREGATE target_action=old_syntax
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEAGGREGATE07934
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/create_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/create_aggregate.yaml
-- primary_obligation_id: CAGG-EXT|07934|actual_execution|DROP_AGGREGATE_IF_EXISTS
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP AGGREGATE IF EXISTS createaggregate_07934_agg(numeric);
DROP FUNCTION IF EXISTS createaggregate_07934_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_07934_ffunc(numeric);
DROP FUNCTION IF EXISTS createaggregate_07934_combine(numeric, numeric);
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FUNCTION createaggregate_07934_sfunc(text, text) RETURNS numeric AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_07934_ffunc(numeric) RETURNS numeric AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_07934_combine(numeric, numeric) RETURNS numeric AS $$ SELECT $1 $$ LANGUAGE SQL;
-- 3. 执行唯一获得覆盖信用的 CREATE AGGREGATE。
-- primary-target-begin
CREATE OR REPLACE AGGREGATE createaggregate_07934_agg (BASETYPE = numeric) (BASETYPE = numeric, SFUNC = createaggregate_07934_sfunc, STYPE = numeric, FINALFUNC = createaggregate_07934_ffunc, COMBINEFUNC = createaggregate_07934_combine);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS agg_executable FROM (SELECT createaggregate_07934_agg(NULL::numeric) AS r) s ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP AGGREGATE IF EXISTS createaggregate_07934_agg(numeric);
DROP FUNCTION IF EXISTS createaggregate_07934_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_07934_ffunc(numeric);
DROP FUNCTION IF EXISTS createaggregate_07934_combine(numeric, numeric);
