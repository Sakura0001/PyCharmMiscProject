-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER SCHEMA privilege_level=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERSCHEMA03647
-- source_md: skills/pg-sql-generation/references/statements/ddl/schema/alter_schema.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/schema/alter_schema.yaml
-- primary_obligation_id: AS-EXT|03647|current_schema_query|DROP_SCHEMA_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SCHEMA IF EXISTS "alterschema_03647_dotted.sch" CASCADE;
DROP SCHEMA IF EXISTS alterschema_03647_newsch CASCADE;
DROP OWNED BY alterschema_03647_actor CASCADE;
DROP ROLE IF EXISTS alterschema_03647_actor;
DROP OWNED BY alterschema_03647_schowner CASCADE;
DROP ROLE IF EXISTS alterschema_03647_schowner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterschema_03647_schowner LOGIN;
CREATE ROLE alterschema_03647_actor LOGIN NOSUPERUSER;
CREATE SCHEMA "alterschema_03647_dotted.sch";
ALTER SCHEMA "alterschema_03647_dotted.sch" OWNER TO alterschema_03647_schowner;
CREATE VIEW "alterschema_03647_dotted.sch".alterschema_03647_v AS SELECT 1 AS alterschema_03647_vcol;
SET ROLE alterschema_03647_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER SCHEMA。
-- primary-target-begin
ALTER SCHEMA "alterschema_03647_dotted.sch" RENAME TO alterschema_03647_newsch;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SET search_path TO "alterschema_03647_dotted.sch"; SELECT current_schema() = 'alterschema_03647_dotted.sch' AS in_target_schema;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS "alterschema_03647_dotted.sch" CASCADE;
DROP SCHEMA IF EXISTS alterschema_03647_newsch CASCADE;
DROP OWNED BY alterschema_03647_actor CASCADE;
DROP ROLE IF EXISTS alterschema_03647_actor;
DROP OWNED BY alterschema_03647_schowner CASCADE;
DROP ROLE IF EXISTS alterschema_03647_schowner;
