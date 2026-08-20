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
-- case_id: CREATEAGGREGATE00802
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/create_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/create_aggregate.yaml
-- primary_obligation_id: CAGG-EXT|00802|pg_proc_query|DROP_AGGREGATE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP AGGREGATE createaggregate_00802_agg(integer);
DROP FUNCTION IF EXISTS createaggregate_00802_nsp.createaggregate_00802_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_00802_ffunc(integer);
DROP FUNCTION IF EXISTS createaggregate_00802_combine(integer, integer);
DROP OWNED BY createaggregate_00802_actor CASCADE;
DROP ROLE IF EXISTS createaggregate_00802_actor;
DROP SCHEMA IF EXISTS createaggregate_00802_nsp CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS createaggregate_00802_nsp;
CREATE ROLE createaggregate_00802_actor LOGIN NOSUPERUSER;
GRANT USAGE ON SCHEMA public TO createaggregate_00802_actor;
GRANT USAGE ON SCHEMA createaggregate_00802_nsp TO createaggregate_00802_actor;
CREATE FUNCTION createaggregate_00802_nsp.createaggregate_00802_sfunc(text, text) RETURNS integer AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_00802_ffunc(integer) RETURNS integer AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_00802_combine(integer, integer) RETURNS integer AS $$ SELECT $1 $$ LANGUAGE SQL;
SET ROLE createaggregate_00802_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE AGGREGATE。
-- primary-target-begin
CREATE AGGREGATE createaggregate_00802_agg (integer, integer) (SFUNC = createaggregate_00802_nsp.createaggregate_00802_sfunc, STYPE = integer, FINALFUNC = createaggregate_00802_ffunc, COMBINEFUNC = createaggregate_00802_combine);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) AS proc_exists FROM pg_catalog.pg_proc WHERE proname = 'createaggregate_00802_agg' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP AGGREGATE createaggregate_00802_agg(integer);
DROP FUNCTION IF EXISTS createaggregate_00802_nsp.createaggregate_00802_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_00802_ffunc(integer);
DROP FUNCTION IF EXISTS createaggregate_00802_combine(integer, integer);
DROP OWNED BY createaggregate_00802_actor CASCADE;
DROP ROLE IF EXISTS createaggregate_00802_actor;
DROP SCHEMA IF EXISTS createaggregate_00802_nsp CASCADE;
