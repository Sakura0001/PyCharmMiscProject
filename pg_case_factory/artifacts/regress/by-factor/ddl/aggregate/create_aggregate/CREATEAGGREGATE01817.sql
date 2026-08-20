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
-- case_id: CREATEAGGREGATE01817
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/create_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/create_aggregate.yaml
-- primary_obligation_id: CAGG-EXT|01817|pg_aggregate_catalog_query|DROP_AGGREGATE_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP AGGREGATE IF EXISTS "createaggregate_01817_Mixed Agg"(boolean);
DROP FUNCTION IF EXISTS createaggregate_01817_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_01817_ffunc(boolean);
DROP FUNCTION IF EXISTS createaggregate_01817_combine(boolean, boolean);
DROP OWNED BY createaggregate_01817_actor CASCADE;
DROP ROLE IF EXISTS createaggregate_01817_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createaggregate_01817_actor LOGIN NOSUPERUSER;
GRANT USAGE ON SCHEMA public TO createaggregate_01817_actor;
CREATE FUNCTION createaggregate_01817_sfunc(text, text) RETURNS boolean AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_01817_ffunc(boolean) RETURNS boolean AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_01817_combine(boolean, boolean) RETURNS boolean AS $$ SELECT $1 $$ LANGUAGE SQL;
SET ROLE createaggregate_01817_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE AGGREGATE。
-- primary-target-begin
CREATE OR REPLACE AGGREGATE "createaggregate_01817_Mixed Agg" (boolean, boolean) (SFUNC = createaggregate_01817_sfunc, STYPE = boolean, FINALFUNC = createaggregate_01817_ffunc, COMBINEFUNC = createaggregate_01817_combine);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) AS agg_exists FROM pg_catalog.pg_aggregate a JOIN pg_catalog.pg_proc p ON a.aggfnoid = p.oid WHERE p.proname = 'createaggregate_01817_Mixed Agg' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP AGGREGATE IF EXISTS "createaggregate_01817_Mixed Agg"(boolean);
DROP FUNCTION IF EXISTS createaggregate_01817_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_01817_ffunc(boolean);
DROP FUNCTION IF EXISTS createaggregate_01817_combine(boolean, boolean);
DROP OWNED BY createaggregate_01817_actor CASCADE;
DROP ROLE IF EXISTS createaggregate_01817_actor;
