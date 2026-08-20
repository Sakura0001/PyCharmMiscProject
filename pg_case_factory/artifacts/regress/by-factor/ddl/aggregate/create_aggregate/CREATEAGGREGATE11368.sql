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
-- case_id: CREATEAGGREGATE11368
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/create_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/create_aggregate.yaml
-- primary_obligation_id: CAGG-EXT|11368|pg_proc_query|DROP_AGGREGATE
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP AGGREGATE "order"(text);
DROP FUNCTION IF EXISTS createaggregate_11368_nsp.createaggregate_11368_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_11368_ffunc(text);
DROP FUNCTION IF EXISTS createaggregate_11368_combine(text, text);
DROP SCHEMA IF EXISTS createaggregate_11368_nsp CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS createaggregate_11368_nsp;
CREATE FUNCTION createaggregate_11368_nsp.createaggregate_11368_sfunc(text, text) RETURNS text AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_11368_ffunc(text) RETURNS text AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_11368_combine(text, text) RETURNS text AS $$ SELECT $1 $$ LANGUAGE SQL;
-- 3. 执行唯一获得覆盖信用的 CREATE AGGREGATE。
-- primary-target-begin
CREATE OR REPLACE AGGREGATE "order" (text) (SFUNC = createaggregate_11368_nsp.createaggregate_11368_sfunc, STYPE = text, FINALFUNC = createaggregate_11368_ffunc, COMBINEFUNC = createaggregate_11368_combine);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS proc_exists FROM pg_catalog.pg_proc WHERE proname = 'order' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP AGGREGATE "order"(text);
DROP FUNCTION IF EXISTS createaggregate_11368_nsp.createaggregate_11368_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_11368_ffunc(text);
DROP FUNCTION IF EXISTS createaggregate_11368_combine(text, text);
DROP SCHEMA IF EXISTS createaggregate_11368_nsp CASCADE;
