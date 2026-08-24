-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE SCHEMA target_action=create_auth_schema
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATESCHEMA06221
-- source_md: skills/pg-sql-generation/references/statements/ddl/schema/create_schema.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/schema/create_schema.yaml
-- primary_obligation_id: CSCHEMA-EXT|06221|pg_namespace_catalog_query|DROP_SCHEMA_CASCADE
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SCHEMA IF EXISTS "createschema_06221_select" CASCADE;
DROP OWNED BY createschema_06221_owner CASCADE;
DROP ROLE IF EXISTS createschema_06221_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createschema_06221_owner LOGIN;
-- 3. 执行唯一获得覆盖信用的 CREATE SCHEMA。
-- primary-target-begin
CREATE SCHEMA AUTHORIZATION CURRENT_USER CREATE VIEW createschema_06221_v AS SELECT 1 AS col;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS schema_state FROM pg_catalog.pg_namespace WHERE nspname = 'createschema_06221_select' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP SCHEMA "createschema_06221_select" CASCADE;
DROP OWNED BY createschema_06221_owner CASCADE;
DROP ROLE IF EXISTS createschema_06221_owner;
