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
-- case_id: CREATEAGGREGATE01184
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/create_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/create_aggregate.yaml
-- primary_obligation_id: CAGG-EXT|01184|actual_execution|DROP_AGGREGATE_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP AGGREGATE IF EXISTS createaggregate_01184_agg(numeric);
DROP FUNCTION IF EXISTS createaggregate_01184_nsp.createaggregate_01184_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_01184_ffunc(numeric);
DROP FUNCTION IF EXISTS createaggregate_01184_combine(numeric, numeric);
DROP OWNED BY createaggregate_01184_actor CASCADE;
DROP ROLE IF EXISTS createaggregate_01184_actor;
DROP SCHEMA IF EXISTS createaggregate_01184_nsp CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS createaggregate_01184_nsp;
CREATE ROLE createaggregate_01184_actor LOGIN NOSUPERUSER;
GRANT USAGE ON SCHEMA public TO createaggregate_01184_actor;
GRANT USAGE ON SCHEMA createaggregate_01184_nsp TO createaggregate_01184_actor;
CREATE FUNCTION createaggregate_01184_nsp.createaggregate_01184_sfunc(text, text) RETURNS numeric AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_01184_ffunc(numeric) RETURNS numeric AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_01184_combine(numeric, numeric) RETURNS numeric AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE AGGREGATE createaggregate_01184_agg (numeric, numeric) (SFUNC = createaggregate_01184_nsp.createaggregate_01184_sfunc, STYPE = numeric, FINALFUNC = createaggregate_01184_ffunc, COMBINEFUNC = createaggregate_01184_combine);
SET ROLE createaggregate_01184_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE AGGREGATE。
-- primary-target-begin
CREATE OR REPLACE AGGREGATE createaggregate_01184_agg (numeric, numeric) (SFUNC = createaggregate_01184_nsp.createaggregate_01184_sfunc, STYPE = numeric, FINALFUNC = createaggregate_01184_ffunc, COMBINEFUNC = createaggregate_01184_combine);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP AGGREGATE IF EXISTS createaggregate_01184_agg(numeric);
DROP FUNCTION IF EXISTS createaggregate_01184_nsp.createaggregate_01184_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_01184_ffunc(numeric);
DROP FUNCTION IF EXISTS createaggregate_01184_combine(numeric, numeric);
DROP OWNED BY createaggregate_01184_actor CASCADE;
DROP ROLE IF EXISTS createaggregate_01184_actor;
DROP SCHEMA IF EXISTS createaggregate_01184_nsp CASCADE;
