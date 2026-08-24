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
-- case_id: CREATEAGGREGATE04115
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/create_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/create_aggregate.yaml
-- primary_obligation_id: CAGG-EXT|04115|pg_proc_query|DROP_AGGREGATE_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP AGGREGATE IF EXISTS "order"(text);
DROP FUNCTION IF EXISTS createaggregate_04115_nsp.createaggregate_04115_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_04115_ffunc(text);
DROP FUNCTION IF EXISTS createaggregate_04115_combine(text, text);
DROP OWNED BY createaggregate_04115_actor CASCADE;
DROP ROLE IF EXISTS createaggregate_04115_actor;
DROP SCHEMA IF EXISTS createaggregate_04115_nsp CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS createaggregate_04115_nsp;
CREATE ROLE createaggregate_04115_actor LOGIN NOSUPERUSER;
GRANT USAGE ON SCHEMA public TO createaggregate_04115_actor;
GRANT USAGE ON SCHEMA createaggregate_04115_nsp TO createaggregate_04115_actor;
CREATE FUNCTION createaggregate_04115_nsp.createaggregate_04115_sfunc(text, text) RETURNS text AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_04115_ffunc(text) RETURNS text AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_04115_combine(text, text) RETURNS text AS $$ SELECT $1 $$ LANGUAGE SQL;
SET ROLE createaggregate_04115_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE AGGREGATE。
-- primary-target-begin
CREATE AGGREGATE "order" (text, text) (SFUNC = createaggregate_04115_nsp.createaggregate_04115_sfunc, STYPE = text, FINALFUNC = createaggregate_04115_ffunc, COMBINEFUNC = createaggregate_04115_combine);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) AS proc_exists FROM pg_catalog.pg_proc WHERE proname = 'order' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP AGGREGATE IF EXISTS "order"(text);
DROP FUNCTION IF EXISTS createaggregate_04115_nsp.createaggregate_04115_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_04115_ffunc(text);
DROP FUNCTION IF EXISTS createaggregate_04115_combine(text, text);
DROP OWNED BY createaggregate_04115_actor CASCADE;
DROP ROLE IF EXISTS createaggregate_04115_actor;
DROP SCHEMA IF EXISTS createaggregate_04115_nsp CASCADE;
