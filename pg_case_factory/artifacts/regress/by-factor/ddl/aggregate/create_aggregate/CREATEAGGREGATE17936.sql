-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE AGGREGATE privilege_level=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEAGGREGATE17936
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/create_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/create_aggregate.yaml
-- primary_obligation_id: CAGG-EXT|17936|pg_aggregate_catalog_query|DROP_AGGREGATE_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP AGGREGATE IF EXISTS createaggregate_17936_nsp.createaggregate_17936_agg;
DROP FUNCTION IF EXISTS createaggregate_17936_nsp.createaggregate_17936_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_17936_ffunc(float8);
DROP FUNCTION IF EXISTS createaggregate_17936_combine(float8, float8);
DROP OWNED BY createaggregate_17936_actor CASCADE;
DROP ROLE IF EXISTS createaggregate_17936_actor;
DROP SCHEMA IF EXISTS createaggregate_17936_nsp CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS createaggregate_17936_nsp;
CREATE ROLE createaggregate_17936_actor LOGIN NOSUPERUSER;
GRANT USAGE ON SCHEMA public TO createaggregate_17936_actor;
GRANT USAGE ON SCHEMA createaggregate_17936_nsp TO createaggregate_17936_actor;
CREATE FUNCTION createaggregate_17936_nsp.createaggregate_17936_sfunc(text, text) RETURNS float8 AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_17936_ffunc(float8) RETURNS float8 AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_17936_combine(float8, float8) RETURNS float8 AS $$ SELECT $1 $$ LANGUAGE SQL;
SET ROLE createaggregate_17936_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE AGGREGATE。
-- primary-target-begin
CREATE AGGREGATE createaggregate_17936_nsp.createaggregate_17936_agg () (SFUNC = createaggregate_17936_nsp.createaggregate_17936_sfunc, STYPE = float8, FINALFUNC = createaggregate_17936_ffunc, COMBINEFUNC = createaggregate_17936_combine);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) AS agg_exists FROM pg_catalog.pg_aggregate a JOIN pg_catalog.pg_proc p ON a.aggfnoid = p.oid WHERE p.proname = 'createaggregate_17936_agg' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP AGGREGATE IF EXISTS createaggregate_17936_nsp.createaggregate_17936_agg;
DROP FUNCTION IF EXISTS createaggregate_17936_nsp.createaggregate_17936_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_17936_ffunc(float8);
DROP FUNCTION IF EXISTS createaggregate_17936_combine(float8, float8);
DROP OWNED BY createaggregate_17936_actor CASCADE;
DROP ROLE IF EXISTS createaggregate_17936_actor;
DROP SCHEMA IF EXISTS createaggregate_17936_nsp CASCADE;
