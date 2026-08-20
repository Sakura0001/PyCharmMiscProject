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
-- case_id: ALTERSCHEMA01560
-- source_md: skills/pg-sql-generation/references/statements/ddl/schema/alter_schema.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/schema/alter_schema.yaml
-- primary_obligation_id: AS-EXT|01560|current_schema_query|DROP_SCHEMA_CASCADE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterschema_01560_tab CASCADE;
DROP SCHEMA IF EXISTS "alterschema_01560_dotted.sch" CASCADE;
DROP OWNED BY alterschema_01560_newowner CASCADE;
DROP ROLE IF EXISTS alterschema_01560_newowner;
DROP OWNED BY alterschema_01560_schowner CASCADE;
DROP ROLE IF EXISTS alterschema_01560_schowner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterschema_01560_schowner LOGIN;
CREATE ROLE alterschema_01560_newowner LOGIN;
GRANT CREATE ON DATABASE pgcf TO alterschema_01560_newowner;
CREATE SCHEMA "alterschema_01560_dotted.sch";
ALTER SCHEMA "alterschema_01560_dotted.sch" OWNER TO alterschema_01560_schowner;
SET search_path TO "alterschema_01560_dotted.sch";
CREATE TABLE alterschema_01560_tab (alterschema_01560_col integer);
RESET search_path;
SET ROLE alterschema_01560_schowner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER SCHEMA。
-- primary-target-begin
ALTER SCHEMA "alterschema_01560_dotted.sch" OWNER TO alterschema_01560_newowner;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SET search_path TO "alterschema_01560_dotted.sch"; SELECT current_schema() = 'alterschema_01560_dotted.sch' AS in_target_schema;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS "alterschema_01560_dotted.sch" CASCADE;
DROP OWNED BY alterschema_01560_newowner CASCADE;
DROP ROLE IF EXISTS alterschema_01560_newowner;
DROP OWNED BY alterschema_01560_schowner CASCADE;
DROP ROLE IF EXISTS alterschema_01560_schowner;
DROP TABLE IF EXISTS alterschema_01560_tab CASCADE;
