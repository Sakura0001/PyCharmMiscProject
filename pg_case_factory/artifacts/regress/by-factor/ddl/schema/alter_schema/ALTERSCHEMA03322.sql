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
-- case_id: ALTERSCHEMA03322
-- source_md: skills/pg-sql-generation/references/statements/ddl/schema/alter_schema.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/schema/alter_schema.yaml
-- primary_obligation_id: AS-EXT|03322|current_schema_query|DROP_SCHEMA
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SCHEMA IF EXISTS "alterschema_03322_dotted.sch" CASCADE;
DROP OWNED BY alterschema_03322_newowner CASCADE;
DROP ROLE IF EXISTS alterschema_03322_newowner;
DROP OWNED BY alterschema_03322_actor CASCADE;
DROP ROLE IF EXISTS alterschema_03322_actor;
DROP OWNED BY alterschema_03322_schowner CASCADE;
DROP ROLE IF EXISTS alterschema_03322_schowner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterschema_03322_schowner LOGIN;
CREATE ROLE alterschema_03322_actor LOGIN NOSUPERUSER;
CREATE ROLE alterschema_03322_newowner LOGIN;
CREATE SCHEMA "alterschema_03322_dotted.sch";
ALTER SCHEMA "alterschema_03322_dotted.sch" OWNER TO alterschema_03322_schowner;
CREATE VIEW "alterschema_03322_dotted.sch".alterschema_03322_v AS SELECT 1 AS alterschema_03322_vcol;
SET ROLE alterschema_03322_actor;
RESET ROLE;
SET ROLE alterschema_03322_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER SCHEMA。
-- primary-target-begin
ALTER SCHEMA "alterschema_03322_dotted.sch" OWNER TO alterschema_03322_newowner;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SET search_path TO "alterschema_03322_dotted.sch"; SELECT current_schema() = 'alterschema_03322_dotted.sch' AS in_target_schema;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS "alterschema_03322_dotted.sch" CASCADE;
DROP OWNED BY alterschema_03322_newowner CASCADE;
DROP ROLE IF EXISTS alterschema_03322_newowner;
DROP OWNED BY alterschema_03322_actor CASCADE;
DROP ROLE IF EXISTS alterschema_03322_actor;
DROP OWNED BY alterschema_03322_schowner CASCADE;
DROP ROLE IF EXISTS alterschema_03322_schowner;
