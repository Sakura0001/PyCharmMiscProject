-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER SCHEMA rename_privilege=owner_no_CREATE_on_db
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERSCHEMA02477
-- source_md: skills/pg-sql-generation/references/statements/ddl/schema/alter_schema.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/schema/alter_schema.yaml
-- primary_obligation_id: AS-EXT|02477|current_schema_query|DROP_SCHEMA_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterschema_02477_tab CASCADE;
DROP SCHEMA IF EXISTS "alterschema_02477_Mixed Schema" CASCADE;
DROP SCHEMA IF EXISTS alterschema_02477_newsch CASCADE;
DROP OWNED BY alterschema_02477_schowner CASCADE;
DROP ROLE IF EXISTS alterschema_02477_schowner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterschema_02477_schowner LOGIN;
CREATE SCHEMA "alterschema_02477_Mixed Schema";
ALTER SCHEMA "alterschema_02477_Mixed Schema" OWNER TO alterschema_02477_schowner;
SET search_path TO "alterschema_02477_Mixed Schema";
CREATE TABLE alterschema_02477_tab (alterschema_02477_col integer);
RESET search_path;
SET ROLE alterschema_02477_schowner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER SCHEMA。
-- primary-target-begin
ALTER SCHEMA "alterschema_02477_Mixed Schema" RENAME TO alterschema_02477_newsch;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SET search_path TO "alterschema_02477_Mixed Schema"; SELECT current_schema() = 'alterschema_02477_Mixed Schema' AS in_target_schema;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS "alterschema_02477_Mixed Schema" CASCADE;
DROP SCHEMA IF EXISTS alterschema_02477_newsch CASCADE;
DROP OWNED BY alterschema_02477_schowner CASCADE;
DROP ROLE IF EXISTS alterschema_02477_schowner;
DROP TABLE IF EXISTS alterschema_02477_tab CASCADE;
