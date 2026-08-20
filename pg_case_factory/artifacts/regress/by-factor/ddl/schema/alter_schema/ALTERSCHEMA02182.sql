-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER SCHEMA new_owner_db_privilege=no_CREATE_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERSCHEMA02182
-- source_md: skills/pg-sql-generation/references/statements/ddl/schema/alter_schema.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/schema/alter_schema.yaml
-- primary_obligation_id: AS-EXT|02182|pg_namespace_catalog_query|DROP_SCHEMA
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterschema_02182_tab CASCADE;
DROP SCHEMA IF EXISTS "alterschema_02182_Mixed Schema" CASCADE;
DROP OWNED BY alterschema_02182_newowner CASCADE;
DROP ROLE IF EXISTS alterschema_02182_newowner;
DROP OWNED BY alterschema_02182_schowner CASCADE;
DROP ROLE IF EXISTS alterschema_02182_schowner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterschema_02182_schowner LOGIN;
CREATE ROLE alterschema_02182_newowner LOGIN;
CREATE SCHEMA "alterschema_02182_Mixed Schema";
ALTER SCHEMA "alterschema_02182_Mixed Schema" OWNER TO alterschema_02182_schowner;
SET search_path TO "alterschema_02182_Mixed Schema";
CREATE TABLE alterschema_02182_tab (alterschema_02182_col integer);
RESET search_path;
GRANT alterschema_02182_newowner TO alterschema_02182_schowner;
SET ROLE alterschema_02182_schowner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER SCHEMA。
-- primary-target-begin
ALTER SCHEMA "alterschema_02182_Mixed Schema" OWNER TO alterschema_02182_newowner;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS schema_state FROM pg_catalog.pg_namespace WHERE nspname = 'alterschema_02182_Mixed Schema' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS "alterschema_02182_Mixed Schema" CASCADE;
DROP OWNED BY alterschema_02182_newowner CASCADE;
DROP ROLE IF EXISTS alterschema_02182_newowner;
DROP OWNED BY alterschema_02182_schowner CASCADE;
DROP ROLE IF EXISTS alterschema_02182_schowner;
DROP TABLE IF EXISTS alterschema_02182_tab CASCADE;
