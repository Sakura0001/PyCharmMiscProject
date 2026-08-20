-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER SCHEMA target_action=rename
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERSCHEMA02830
-- source_md: skills/pg-sql-generation/references/statements/ddl/schema/alter_schema.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/schema/alter_schema.yaml
-- primary_obligation_id: AS-EXT|02830|pg_namespace_catalog_query|DROP_SCHEMA
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterschema_02830_tab CASCADE;
DROP SCHEMA IF EXISTS "alterschema_02830_Mixed Schema" CASCADE;
DROP SCHEMA IF EXISTS alterschema_02830_newsch CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA "alterschema_02830_Mixed Schema";
SET search_path TO "alterschema_02830_Mixed Schema";
CREATE TABLE alterschema_02830_tab (alterschema_02830_col integer);
RESET search_path;
-- 3. 执行唯一获得覆盖信用的 ALTER SCHEMA。
-- primary-target-begin
ALTER SCHEMA "alterschema_02830_Mixed Schema" RENAME TO alterschema_02830_newsch;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS schema_state FROM pg_catalog.pg_namespace WHERE nspname = 'alterschema_02830_newsch' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP SCHEMA IF EXISTS "alterschema_02830_Mixed Schema" CASCADE;
DROP SCHEMA IF EXISTS alterschema_02830_newsch CASCADE;
DROP TABLE IF EXISTS alterschema_02830_tab CASCADE;
