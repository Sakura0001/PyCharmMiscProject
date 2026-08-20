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
-- case_id: ALTERSCHEMA03985
-- source_md: skills/pg-sql-generation/references/statements/ddl/schema/alter_schema.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/schema/alter_schema.yaml
-- primary_obligation_id: AS-EXT|03985|information_schema_schemata|DROP_SCHEMA
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SCHEMA IF EXISTS "alterschema_03985_Mixed Schema" CASCADE;
DROP OWNED BY alterschema_03985_schowner CASCADE;
DROP ROLE IF EXISTS alterschema_03985_schowner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterschema_03985_schowner LOGIN;
CREATE SCHEMA "alterschema_03985_Mixed Schema";
ALTER SCHEMA "alterschema_03985_Mixed Schema" OWNER TO alterschema_03985_schowner;
CREATE VIEW "alterschema_03985_Mixed Schema".alterschema_03985_v AS SELECT 1 AS alterschema_03985_vcol;
SET ROLE alterschema_03985_schowner;
-- 3. 执行唯一获得覆盖信用的 ALTER SCHEMA。
-- primary-target-begin
ALTER SCHEMA "alterschema_03985_Mixed Schema" OWNER TO CURRENT_USER;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS schema_state FROM information_schema.schemata WHERE schema_name = 'alterschema_03985_Mixed Schema' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS "alterschema_03985_Mixed Schema" CASCADE;
DROP OWNED BY alterschema_03985_schowner CASCADE;
DROP ROLE IF EXISTS alterschema_03985_schowner;
