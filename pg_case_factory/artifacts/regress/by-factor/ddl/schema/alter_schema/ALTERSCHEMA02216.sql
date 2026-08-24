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
-- case_id: ALTERSCHEMA02216
-- source_md: skills/pg-sql-generation/references/statements/ddl/schema/alter_schema.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/schema/alter_schema.yaml
-- primary_obligation_id: AS-EXT|02216|current_schema_query|DROP_SCHEMA_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterschema_02216_sch.alterschema_02216_tab CASCADE;
DROP SCHEMA IF EXISTS alterschema_02216_sch CASCADE;
DROP OWNED BY alterschema_02216_newowner CASCADE;
DROP ROLE IF EXISTS alterschema_02216_newowner;
DROP OWNED BY alterschema_02216_schowner CASCADE;
DROP ROLE IF EXISTS alterschema_02216_schowner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterschema_02216_schowner LOGIN;
CREATE ROLE alterschema_02216_newowner LOGIN;
CREATE SCHEMA alterschema_02216_sch;
ALTER SCHEMA alterschema_02216_sch OWNER TO alterschema_02216_schowner;
CREATE TABLE alterschema_02216_sch.alterschema_02216_tab (alterschema_02216_col integer);
GRANT alterschema_02216_newowner TO alterschema_02216_schowner;
SET ROLE alterschema_02216_schowner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER SCHEMA。
-- primary-target-begin
ALTER SCHEMA alterschema_02216_sch OWNER TO alterschema_02216_newowner;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SET search_path TO "alterschema_02216_sch"; SELECT current_schema() = 'alterschema_02216_sch' AS in_target_schema;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS alterschema_02216_sch CASCADE;
DROP OWNED BY alterschema_02216_newowner CASCADE;
DROP ROLE IF EXISTS alterschema_02216_newowner;
DROP OWNED BY alterschema_02216_schowner CASCADE;
DROP ROLE IF EXISTS alterschema_02216_schowner;
DROP TABLE IF EXISTS alterschema_02216_sch.alterschema_02216_tab CASCADE;
