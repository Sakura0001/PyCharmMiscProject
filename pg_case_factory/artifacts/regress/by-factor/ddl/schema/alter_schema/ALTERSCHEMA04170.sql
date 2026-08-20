-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER SCHEMA target_action=owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERSCHEMA04170
-- source_md: skills/pg-sql-generation/references/statements/ddl/schema/alter_schema.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/schema/alter_schema.yaml
-- primary_obligation_id: AS-EXT|04170|current_schema_query|DROP_SCHEMA_CASCADE
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SCHEMA IF EXISTS "alterschema_04170_Mixed Schema" CASCADE;
DROP OWNED BY alterschema_04170_newowner CASCADE;
DROP ROLE IF EXISTS alterschema_04170_newowner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SCHEMA "alterschema_04170_Mixed Schema";
CREATE VIEW "alterschema_04170_Mixed Schema".alterschema_04170_v AS SELECT 1 AS alterschema_04170_vcol;
-- 3. 执行唯一获得覆盖信用的 ALTER SCHEMA。
-- primary-target-begin
ALTER SCHEMA "alterschema_04170_Mixed Schema" OWNER TO alterschema_04170_newowner;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SET search_path TO "alterschema_04170_Mixed Schema"; SELECT current_schema() = 'alterschema_04170_Mixed Schema' AS in_target_schema;
-- 5. 清理全部本编号对象。
DROP SCHEMA IF EXISTS "alterschema_04170_Mixed Schema" CASCADE;
DROP OWNED BY alterschema_04170_newowner CASCADE;
DROP ROLE IF EXISTS alterschema_04170_newowner;
