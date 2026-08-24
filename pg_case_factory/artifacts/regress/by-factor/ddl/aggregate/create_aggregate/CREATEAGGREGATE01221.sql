-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE AGGREGATE target_action=regular
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEAGGREGATE01221
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/create_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/create_aggregate.yaml
-- primary_obligation_id: CAGG-EXT|01221|actual_execution|DROP_AGGREGATE_CASCADE
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP AGGREGATE createaggregate_01221_agg(numeric) CASCADE;
DROP FUNCTION IF EXISTS createaggregate_01221_nsp.createaggregate_01221_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_01221_ffunc(numeric);
DROP FUNCTION IF EXISTS createaggregate_01221_combine(numeric, numeric);
DROP SCHEMA IF EXISTS createaggregate_01221_nsp CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS createaggregate_01221_nsp;
CREATE FUNCTION createaggregate_01221_nsp.createaggregate_01221_sfunc(text, text) RETURNS numeric AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_01221_ffunc(numeric) RETURNS numeric AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_01221_combine(numeric, numeric) RETURNS numeric AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE AGGREGATE createaggregate_01221_agg (numeric, numeric) (SFUNC = createaggregate_01221_nsp.createaggregate_01221_sfunc, STYPE = numeric, FINALFUNC = createaggregate_01221_ffunc, COMBINEFUNC = createaggregate_01221_combine);
-- 3. 执行唯一获得覆盖信用的 CREATE AGGREGATE。
-- primary-target-begin
CREATE OR REPLACE AGGREGATE createaggregate_01221_agg (numeric, numeric) (SFUNC = createaggregate_01221_nsp.createaggregate_01221_sfunc, STYPE = numeric, FINALFUNC = createaggregate_01221_ffunc, COMBINEFUNC = createaggregate_01221_combine);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS agg_executable FROM (SELECT createaggregate_01221_agg(NULL::numeric) AS r) s ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP AGGREGATE createaggregate_01221_agg(numeric) CASCADE;
DROP FUNCTION IF EXISTS createaggregate_01221_nsp.createaggregate_01221_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_01221_ffunc(numeric);
DROP FUNCTION IF EXISTS createaggregate_01221_combine(numeric, numeric);
DROP SCHEMA IF EXISTS createaggregate_01221_nsp CASCADE;
