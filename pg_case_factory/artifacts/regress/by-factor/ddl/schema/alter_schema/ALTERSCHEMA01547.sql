-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER SCHEMA owner_change_privilege=cannot_SET_ROLE_to_new_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERSCHEMA01547
-- source_md: skills/pg-sql-generation/references/statements/ddl/schema/alter_schema.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/schema/alter_schema.yaml
-- primary_obligation_id: AS-EXT|01547|information_schema_schemata|DROP_SCHEMA_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterschema_01547_tab CASCADE;
DROP SCHEMA IF EXISTS "select" CASCADE;
DROP OWNED BY alterschema_01547_newowner CASCADE;
DROP ROLE IF EXISTS alterschema_01547_newowner;
DROP OWNED BY alterschema_01547_schowner CASCADE;
DROP ROLE IF EXISTS alterschema_01547_schowner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterschema_01547_schowner LOGIN;
CREATE ROLE alterschema_01547_newowner LOGIN;
GRANT CREATE ON DATABASE pgcf TO alterschema_01547_newowner;
CREATE SCHEMA "select";
ALTER SCHEMA "select" OWNER TO alterschema_01547_schowner;
SET search_path TO "select";
CREATE TABLE alterschema_01547_tab (alterschema_01547_col integer);
RESET search_path;
SET ROLE alterschema_01547_schowner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER SCHEMA。
-- primary-target-begin
ALTER SCHEMA "select" OWNER TO alterschema_01547_newowner;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS schema_state FROM information_schema.schemata WHERE schema_name = 'select' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS "select" CASCADE;
DROP OWNED BY alterschema_01547_newowner CASCADE;
DROP ROLE IF EXISTS alterschema_01547_newowner;
DROP OWNED BY alterschema_01547_schowner CASCADE;
DROP ROLE IF EXISTS alterschema_01547_schowner;
DROP TABLE IF EXISTS alterschema_01547_tab CASCADE;
