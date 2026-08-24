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
-- case_id: CREATEAGGREGATE11046
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/create_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/create_aggregate.yaml
-- primary_obligation_id: CAGG-EXT|11046|pg_proc_query|DROP_AGGREGATE_CASCADE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP AGGREGATE "order"(internal) CASCADE;
DROP FUNCTION IF EXISTS createaggregate_11046_nsp.createaggregate_11046_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_11046_ffunc(internal);
DROP FUNCTION IF EXISTS createaggregate_11046_combine(internal, internal);
DROP OWNED BY createaggregate_11046_actor CASCADE;
DROP ROLE IF EXISTS createaggregate_11046_actor;
DROP SCHEMA IF EXISTS createaggregate_11046_nsp CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS createaggregate_11046_nsp;
CREATE ROLE createaggregate_11046_actor LOGIN NOSUPERUSER;
GRANT USAGE ON SCHEMA public TO createaggregate_11046_actor;
GRANT USAGE ON SCHEMA createaggregate_11046_nsp TO createaggregate_11046_actor;
CREATE FUNCTION createaggregate_11046_nsp.createaggregate_11046_sfunc(text, text) RETURNS internal AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_11046_ffunc(internal) RETURNS internal AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_11046_combine(internal, internal) RETURNS internal AS $$ SELECT $1 $$ LANGUAGE SQL;
SET ROLE createaggregate_11046_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE AGGREGATE。
-- primary-target-begin
CREATE OR REPLACE AGGREGATE "order" (internal) (SFUNC = createaggregate_11046_nsp.createaggregate_11046_sfunc, STYPE = internal, FINALFUNC = createaggregate_11046_ffunc, COMBINEFUNC = createaggregate_11046_combine);
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
DROP AGGREGATE "order"(internal) CASCADE;
DROP FUNCTION IF EXISTS createaggregate_11046_nsp.createaggregate_11046_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_11046_ffunc(internal);
DROP FUNCTION IF EXISTS createaggregate_11046_combine(internal, internal);
DROP OWNED BY createaggregate_11046_actor CASCADE;
DROP ROLE IF EXISTS createaggregate_11046_actor;
DROP SCHEMA IF EXISTS createaggregate_11046_nsp CASCADE;
