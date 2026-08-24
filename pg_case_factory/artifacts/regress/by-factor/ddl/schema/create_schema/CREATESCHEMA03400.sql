-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE SCHEMA privilege_level=non_creator_no_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATESCHEMA03400
-- source_md: skills/pg-sql-generation/references/statements/ddl/schema/create_schema.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/schema/create_schema.yaml
-- primary_obligation_id: CSCHEMA-EXT|03400|current_schema_query|DROP_SCHEMA_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SCHEMA IF EXISTS "createschema_03400_select" CASCADE;
DROP OWNED BY createschema_03400_owner CASCADE;
DROP ROLE IF EXISTS createschema_03400_owner;
DROP OWNED BY createschema_03400_actor CASCADE;
DROP ROLE IF EXISTS createschema_03400_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createschema_03400_owner LOGIN;
CREATE ROLE createschema_03400_actor LOGIN NOSUPERUSER;
GRANT CREATE ON DATABASE pgcf TO createschema_03400_actor;
SET ROLE createschema_03400_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE SCHEMA。
-- primary-target-begin
CREATE SCHEMA "createschema_03400_select" AUTHORIZATION SESSION_USER CREATE VIEW createschema_03400_v AS SELECT 1 AS col;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT current_schema() AS current_schema_name ORDER BY current_schema_name;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS "createschema_03400_select" CASCADE;
DROP OWNED BY createschema_03400_owner CASCADE;
DROP ROLE IF EXISTS createschema_03400_owner;
DROP OWNED BY createschema_03400_actor CASCADE;
DROP ROLE IF EXISTS createschema_03400_actor;
