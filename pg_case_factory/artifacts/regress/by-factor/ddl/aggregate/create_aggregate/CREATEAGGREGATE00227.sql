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
-- case_id: CREATEAGGREGATE00227
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/create_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/create_aggregate.yaml
-- primary_obligation_id: CAGG-EXT|00227|pg_proc_query|DROP_AGGREGATE_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP AGGREGATE IF EXISTS createaggregate_00227_agg(bigint);
DROP FUNCTION IF EXISTS createaggregate_00227_nsp.createaggregate_00227_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_00227_ffunc(bigint);
DROP FUNCTION IF EXISTS createaggregate_00227_combine(bigint, bigint);
DROP OWNED BY createaggregate_00227_actor CASCADE;
DROP ROLE IF EXISTS createaggregate_00227_actor;
DROP SCHEMA IF EXISTS createaggregate_00227_nsp CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS createaggregate_00227_nsp;
CREATE ROLE createaggregate_00227_actor LOGIN NOSUPERUSER;
GRANT USAGE ON SCHEMA public TO createaggregate_00227_actor;
GRANT USAGE ON SCHEMA createaggregate_00227_nsp TO createaggregate_00227_actor;
CREATE FUNCTION createaggregate_00227_nsp.createaggregate_00227_sfunc(text, text) RETURNS bigint AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_00227_ffunc(bigint) RETURNS bigint AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_00227_combine(bigint, bigint) RETURNS bigint AS $$ SELECT $1 $$ LANGUAGE SQL;
SET ROLE createaggregate_00227_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE AGGREGATE。
-- primary-target-begin
CREATE AGGREGATE createaggregate_00227_agg (bigint, bigint) (SFUNC = createaggregate_00227_nsp.createaggregate_00227_sfunc, STYPE = bigint, FINALFUNC = createaggregate_00227_ffunc, COMBINEFUNC = createaggregate_00227_combine);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) AS proc_exists FROM pg_catalog.pg_proc WHERE proname = 'createaggregate_00227_agg' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP AGGREGATE IF EXISTS createaggregate_00227_agg(bigint);
DROP FUNCTION IF EXISTS createaggregate_00227_nsp.createaggregate_00227_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_00227_ffunc(bigint);
DROP FUNCTION IF EXISTS createaggregate_00227_combine(bigint, bigint);
DROP OWNED BY createaggregate_00227_actor CASCADE;
DROP ROLE IF EXISTS createaggregate_00227_actor;
DROP SCHEMA IF EXISTS createaggregate_00227_nsp CASCADE;
