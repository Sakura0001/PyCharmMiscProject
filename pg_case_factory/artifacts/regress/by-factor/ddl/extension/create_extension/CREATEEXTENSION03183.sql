-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE EXTENSION privilege_level=non_superuser_no_create
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEEXTENSION03183
-- source_md: skills/pg-sql-generation/references/statements/ddl/extension/create_extension.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/extension/create_extension.yaml
-- primary_obligation_id: CE-EXT|03183|pg_extension_catalog_query|schema_cleanup
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP EXTENSION IF EXISTS "createextension_03183_select" CASCADE;
DROP SCHEMA IF EXISTS createextension_03183_schema CASCADE;
DROP OWNED BY createextension_03183_actor CASCADE;
DROP ROLE IF EXISTS createextension_03183_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createextension_03183_actor LOGIN NOSUPERUSER;
CREATE SCHEMA IF NOT EXISTS createextension_03183_schema;
SET ROLE createextension_03183_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE EXTENSION。
-- primary-target-begin
CREATE EXTENSION "createextension_03183_select" WITH SCHEMA createextension_03183_schema CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS ext_state FROM pg_catalog.pg_extension WHERE extname = 'createextension_03183_select' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP EXTENSION IF EXISTS "createextension_03183_select" CASCADE;
DROP SCHEMA IF EXISTS createextension_03183_schema CASCADE;
DROP OWNED BY createextension_03183_actor CASCADE;
DROP ROLE IF EXISTS createextension_03183_actor;
