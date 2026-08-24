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
-- case_id: CREATEAGGREGATE12264
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/create_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/create_aggregate.yaml
-- primary_obligation_id: CAGG-EXT|12264|actual_execution|DROP_AGGREGATE_CASCADE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP AGGREGATE createaggregate_12264_nsp.createaggregate_12264_agg(float8) CASCADE;
DROP FUNCTION IF EXISTS createaggregate_12264_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_12264_ffunc(float8);
DROP FUNCTION IF EXISTS createaggregate_12264_combine(float8, float8);
DROP OWNED BY createaggregate_12264_actor CASCADE;
DROP ROLE IF EXISTS createaggregate_12264_actor;
DROP SCHEMA IF EXISTS createaggregate_12264_nsp CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS createaggregate_12264_nsp;
CREATE ROLE createaggregate_12264_actor LOGIN NOSUPERUSER;
GRANT USAGE ON SCHEMA public TO createaggregate_12264_actor;
GRANT USAGE ON SCHEMA createaggregate_12264_nsp TO createaggregate_12264_actor;
CREATE FUNCTION createaggregate_12264_sfunc(text, text) RETURNS float8 AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_12264_ffunc(float8) RETURNS float8 AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_12264_combine(float8, float8) RETURNS float8 AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE AGGREGATE createaggregate_12264_nsp.createaggregate_12264_agg (float8) (SFUNC = createaggregate_12264_sfunc, STYPE = float8, FINALFUNC = createaggregate_12264_ffunc, COMBINEFUNC = createaggregate_12264_combine);
SET ROLE createaggregate_12264_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE AGGREGATE。
-- primary-target-begin
CREATE OR REPLACE AGGREGATE createaggregate_12264_nsp.createaggregate_12264_agg (float8) (SFUNC = createaggregate_12264_sfunc, STYPE = float8, FINALFUNC = createaggregate_12264_ffunc, COMBINEFUNC = createaggregate_12264_combine);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP AGGREGATE createaggregate_12264_nsp.createaggregate_12264_agg(float8) CASCADE;
DROP FUNCTION IF EXISTS createaggregate_12264_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_12264_ffunc(float8);
DROP FUNCTION IF EXISTS createaggregate_12264_combine(float8, float8);
DROP OWNED BY createaggregate_12264_actor CASCADE;
DROP ROLE IF EXISTS createaggregate_12264_actor;
DROP SCHEMA IF EXISTS createaggregate_12264_nsp CASCADE;
