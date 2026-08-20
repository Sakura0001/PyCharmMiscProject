-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE SCHEMA role_dependency=cannot_SET_ROLE
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATESCHEMA00315
-- source_md: skills/pg-sql-generation/references/statements/ddl/schema/create_schema.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/schema/create_schema.yaml
-- primary_obligation_id: CSCHEMA-EXT|00315|pg_namespace_catalog_query|DROP_SCHEMA
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SCHEMA IF EXISTS createschema_00315_s CASCADE;
DROP OWNED BY createschema_00315_owner CASCADE;
DROP ROLE IF EXISTS createschema_00315_owner;
DROP OWNED BY createschema_00315_actor CASCADE;
DROP ROLE IF EXISTS createschema_00315_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createschema_00315_owner LOGIN;
CREATE ROLE createschema_00315_actor LOGIN NOSUPERUSER;
SET ROLE createschema_00315_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE SCHEMA。
-- primary-target-begin
CREATE SCHEMA createschema_00315_s AUTHORIZATION CURRENT_ROLE CREATE TABLE createschema_00315_t (id integer);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS schema_state FROM pg_catalog.pg_namespace WHERE nspname = 'createschema_00315_s' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA createschema_00315_s CASCADE;
DROP OWNED BY createschema_00315_owner CASCADE;
DROP ROLE IF EXISTS createschema_00315_owner;
DROP OWNED BY createschema_00315_actor CASCADE;
DROP ROLE IF EXISTS createschema_00315_actor;
