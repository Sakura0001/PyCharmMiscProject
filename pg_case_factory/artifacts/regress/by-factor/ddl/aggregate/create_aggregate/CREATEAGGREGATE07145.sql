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
-- case_id: CREATEAGGREGATE07145
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/create_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/create_aggregate.yaml
-- primary_obligation_id: CAGG-EXT|07145|pg_aggregate_catalog_query|DROP_AGGREGATE_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P17
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP AGGREGATE IF EXISTS createaggregate_07145_agg(float8);
DROP FUNCTION IF EXISTS createaggregate_07145_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_07145_ffunc(float8);
DROP FUNCTION IF EXISTS createaggregate_07145_combine(float8, float8);
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FUNCTION createaggregate_07145_sfunc(text, text) RETURNS float8 AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_07145_ffunc(float8) RETURNS float8 AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_07145_combine(float8, float8) RETURNS float8 AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE AGGREGATE createaggregate_07145_agg (BASETYPE = float8) (BASETYPE = float8, SFUNC = createaggregate_07145_sfunc, STYPE = float8, FINALFUNC = createaggregate_07145_ffunc, COMBINEFUNC = createaggregate_07145_combine);
CREATE FUNCTION createaggregate_07145_sfunc(float8, text) RETURNS float8 AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE AGGREGATE createaggregate_07145_agg (text) (SFUNC = createaggregate_07145_sfunc, STYPE = float8);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE AGGREGATE。
-- primary-target-begin
CREATE OR REPLACE AGGREGATE createaggregate_07145_agg (BASETYPE = float8) (BASETYPE = float8, SFUNC = createaggregate_07145_sfunc, STYPE = float8, FINALFUNC = createaggregate_07145_ffunc, COMBINEFUNC = createaggregate_07145_combine);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42P17' AS target_sqlstate_matches_expected;
SELECT count(*) AS agg_exists FROM pg_catalog.pg_aggregate a JOIN pg_catalog.pg_proc p ON a.aggfnoid = p.oid WHERE p.proname = 'createaggregate_07145_agg' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP AGGREGATE IF EXISTS createaggregate_07145_agg(float8);
DROP FUNCTION IF EXISTS createaggregate_07145_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_07145_ffunc(float8);
DROP FUNCTION IF EXISTS createaggregate_07145_combine(float8, float8);
