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
-- case_id: CREATEAGGREGATE15299
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/create_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/create_aggregate.yaml
-- primary_obligation_id: CAGG-EXT|15299|pg_aggregate_catalog_query|DROP_AGGREGATE_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P17
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP AGGREGATE IF EXISTS "createaggregate_15299_Mixed Agg";
DROP FUNCTION IF EXISTS createaggregate_15299_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_15299_ffunc(integer);
DROP FUNCTION IF EXISTS createaggregate_15299_combine(integer, integer);
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FUNCTION createaggregate_15299_sfunc(text, text) RETURNS integer AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_15299_ffunc(integer) RETURNS integer AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_15299_combine(integer, integer) RETURNS integer AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE AGGREGATE "createaggregate_15299_Mixed Agg" () (SFUNC = createaggregate_15299_sfunc, STYPE = integer, FINALFUNC = createaggregate_15299_ffunc, COMBINEFUNC = createaggregate_15299_combine);
CREATE FUNCTION createaggregate_15299_sfunc(integer, text) RETURNS integer AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE AGGREGATE "createaggregate_15299_Mixed Agg" (text) (SFUNC = createaggregate_15299_sfunc, STYPE = integer);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE AGGREGATE。
-- primary-target-begin
CREATE OR REPLACE AGGREGATE "createaggregate_15299_Mixed Agg" () (SFUNC = createaggregate_15299_sfunc, STYPE = integer, FINALFUNC = createaggregate_15299_ffunc, COMBINEFUNC = createaggregate_15299_combine);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42P17' AS target_sqlstate_matches_expected;
SELECT count(*) AS agg_exists FROM pg_catalog.pg_aggregate a JOIN pg_catalog.pg_proc p ON a.aggfnoid = p.oid WHERE p.proname = 'createaggregate_15299_Mixed Agg' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP AGGREGATE IF EXISTS "createaggregate_15299_Mixed Agg";
DROP FUNCTION IF EXISTS createaggregate_15299_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_15299_ffunc(integer);
DROP FUNCTION IF EXISTS createaggregate_15299_combine(integer, integer);
