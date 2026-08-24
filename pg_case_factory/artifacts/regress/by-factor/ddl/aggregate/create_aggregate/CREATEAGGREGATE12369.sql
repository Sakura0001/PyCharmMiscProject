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
-- case_id: CREATEAGGREGATE12369
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/create_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/create_aggregate.yaml
-- primary_obligation_id: CAGG-EXT|12369|pg_proc_query|DROP_AGGREGATE_CASCADE
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP AGGREGATE createaggregate_12369_nsp.createaggregate_12369_agg(integer) CASCADE;
DROP FUNCTION IF EXISTS createaggregate_12369_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_12369_ffunc(integer);
DROP FUNCTION IF EXISTS createaggregate_12369_combine(integer, integer);
DROP SCHEMA IF EXISTS createaggregate_12369_nsp CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS createaggregate_12369_nsp;
CREATE FUNCTION createaggregate_12369_sfunc(text, text) RETURNS integer AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_12369_ffunc(integer) RETURNS integer AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_12369_combine(integer, integer) RETURNS integer AS $$ SELECT $1 $$ LANGUAGE SQL;
-- 3. 执行唯一获得覆盖信用的 CREATE AGGREGATE。
-- primary-target-begin
CREATE OR REPLACE AGGREGATE createaggregate_12369_nsp.createaggregate_12369_agg (integer) (SFUNC = createaggregate_12369_sfunc, STYPE = integer, FINALFUNC = createaggregate_12369_ffunc, COMBINEFUNC = createaggregate_12369_combine);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS proc_exists FROM pg_catalog.pg_proc WHERE proname = 'createaggregate_12369_agg' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP AGGREGATE createaggregate_12369_nsp.createaggregate_12369_agg(integer) CASCADE;
DROP FUNCTION IF EXISTS createaggregate_12369_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_12369_ffunc(integer);
DROP FUNCTION IF EXISTS createaggregate_12369_combine(integer, integer);
DROP SCHEMA IF EXISTS createaggregate_12369_nsp CASCADE;
