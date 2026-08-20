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
-- case_id: CREATEAGGREGATE02693
-- source_md: skills/pg-sql-generation/references/statements/ddl/aggregate/create_aggregate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/aggregate/create_aggregate.yaml
-- primary_obligation_id: CAGG-EXT|02693|pg_proc_query|DROP_AGGREGATE_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP AGGREGATE IF EXISTS "createaggregate_02693_Mixed Agg"(text);
DROP FUNCTION IF EXISTS createaggregate_02693_nsp.createaggregate_02693_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_02693_ffunc(text);
DROP FUNCTION IF EXISTS createaggregate_02693_combine(text, text);
DROP OWNED BY createaggregate_02693_actor CASCADE;
DROP ROLE IF EXISTS createaggregate_02693_actor;
DROP SCHEMA IF EXISTS createaggregate_02693_nsp CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS createaggregate_02693_nsp;
CREATE ROLE createaggregate_02693_actor LOGIN NOSUPERUSER;
GRANT USAGE ON SCHEMA public TO createaggregate_02693_actor;
GRANT USAGE ON SCHEMA createaggregate_02693_nsp TO createaggregate_02693_actor;
CREATE FUNCTION createaggregate_02693_nsp.createaggregate_02693_sfunc(text, text) RETURNS text AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_02693_ffunc(text) RETURNS text AS $$ SELECT $1 $$ LANGUAGE SQL;
CREATE FUNCTION createaggregate_02693_combine(text, text) RETURNS text AS $$ SELECT $1 $$ LANGUAGE SQL;
SET ROLE createaggregate_02693_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE AGGREGATE。
-- primary-target-begin
CREATE OR REPLACE AGGREGATE "createaggregate_02693_Mixed Agg" (text, text) (SFUNC = createaggregate_02693_nsp.createaggregate_02693_sfunc, STYPE = text, FINALFUNC = createaggregate_02693_ffunc, COMBINEFUNC = createaggregate_02693_combine);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) AS proc_exists FROM pg_catalog.pg_proc WHERE proname = 'createaggregate_02693_Mixed Agg' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP AGGREGATE IF EXISTS "createaggregate_02693_Mixed Agg"(text);
DROP FUNCTION IF EXISTS createaggregate_02693_nsp.createaggregate_02693_sfunc(text, text);
DROP FUNCTION IF EXISTS createaggregate_02693_ffunc(text);
DROP FUNCTION IF EXISTS createaggregate_02693_combine(text, text);
DROP OWNED BY createaggregate_02693_actor CASCADE;
DROP ROLE IF EXISTS createaggregate_02693_actor;
DROP SCHEMA IF EXISTS createaggregate_02693_nsp CASCADE;
