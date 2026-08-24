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
-- case_id: CREATEAGGREGATE06019
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/create_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/create_aggregate.yaml
-- primary_obligation_id: CAGG-EXT|06019|pg_aggregate_catalog_query|DROP_AGGREGATE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P17
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP AGGREGATE createaggregate_06019_agg(anyelement);
DROP FUNCTION IF EXISTS createaggregate_06019_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_06019_ffunc(anyelement);
DROP FUNCTION IF EXISTS createaggregate_06019_combine(anyelement, anyelement);
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FUNCTION createaggregate_06019_sfunc(text, text) RETURNS anyelement AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_06019_ffunc(anyelement) RETURNS anyelement AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_06019_combine(anyelement, anyelement) RETURNS anyelement AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE AGGREGATE createaggregate_06019_agg (ORDER BY VARIADIC anyelement) (SFUNC = createaggregate_06019_sfunc, STYPE = anyelement, FINALFUNC = createaggregate_06019_ffunc, COMBINEFUNC = createaggregate_06019_combine);
CREATE FUNCTION createaggregate_06019_sfunc(anyelement, text) RETURNS anyelement AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE AGGREGATE createaggregate_06019_agg (text) (SFUNC = createaggregate_06019_sfunc, STYPE = anyelement);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE AGGREGATE。
-- primary-target-begin
CREATE OR REPLACE AGGREGATE createaggregate_06019_agg (ORDER BY VARIADIC anyelement) (SFUNC = createaggregate_06019_sfunc, STYPE = anyelement, FINALFUNC = createaggregate_06019_ffunc, COMBINEFUNC = createaggregate_06019_combine);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42P17' AS target_sqlstate_matches_expected;
SELECT count(*) AS agg_exists FROM pg_catalog.pg_aggregate a JOIN pg_catalog.pg_proc p ON a.aggfnoid = p.oid WHERE p.proname = 'createaggregate_06019_agg' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP AGGREGATE createaggregate_06019_agg(anyelement);
DROP FUNCTION IF EXISTS createaggregate_06019_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_06019_ffunc(anyelement);
DROP FUNCTION IF EXISTS createaggregate_06019_combine(anyelement, anyelement);
