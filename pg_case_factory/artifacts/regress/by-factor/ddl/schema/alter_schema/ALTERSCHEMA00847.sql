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
-- case_id: ALTERSCHEMA00847
-- source_md: skills/pg-sql-generation/references/statements/ddl/schema/alter_schema.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/schema/alter_schema.yaml
-- primary_obligation_id: AS-EXT|00847|current_schema_query|DROP_SCHEMA
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SCHEMA IF EXISTS alterschema_00847_sch CASCADE;
DROP SCHEMA IF EXISTS alterschema_00847_newsch CASCADE;
DROP OWNED BY alterschema_00847_actor CASCADE;
DROP ROLE IF EXISTS alterschema_00847_actor;
DROP OWNED BY alterschema_00847_schowner CASCADE;
DROP ROLE IF EXISTS alterschema_00847_schowner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterschema_00847_schowner LOGIN;
CREATE ROLE alterschema_00847_actor LOGIN NOSUPERUSER;
CREATE SCHEMA alterschema_00847_sch;
ALTER SCHEMA alterschema_00847_sch OWNER TO alterschema_00847_schowner;
SET ROLE alterschema_00847_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER SCHEMA。
-- primary-target-begin
ALTER SCHEMA alterschema_00847_sch RENAME TO alterschema_00847_newsch;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SET search_path TO "alterschema_00847_sch"; SELECT current_schema() = 'alterschema_00847_sch' AS in_target_schema;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS alterschema_00847_sch CASCADE;
DROP SCHEMA IF EXISTS alterschema_00847_newsch CASCADE;
DROP OWNED BY alterschema_00847_actor CASCADE;
DROP ROLE IF EXISTS alterschema_00847_actor;
DROP OWNED BY alterschema_00847_schowner CASCADE;
DROP ROLE IF EXISTS alterschema_00847_schowner;
