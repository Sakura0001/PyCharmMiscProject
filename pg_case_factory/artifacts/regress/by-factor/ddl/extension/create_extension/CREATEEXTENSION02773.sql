-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE EXTENSION version_clause=invalid_version
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEEXTENSION02773
-- source_md: skills/pg-sql-generation/references/statements/ddl/extension/create_extension.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/extension/create_extension.yaml
-- primary_obligation_id: CE-EXT|02773|pg_available_extensions_query|drop_extension
-- expected_outcome: expected_failure
-- expected_sqlstate: 22023
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP EXTENSION IF EXISTS "createextension_02773_MixedExt" CASCADE;
DROP SCHEMA IF EXISTS createextension_02773_schema CASCADE;
DROP OWNED BY createextension_02773_create_user CASCADE;
DROP ROLE IF EXISTS createextension_02773_create_user;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createextension_02773_create_user LOGIN NOSUPERUSER;
GRANT CREATE ON SCHEMA public TO createextension_02773_create_user;
CREATE SCHEMA IF NOT EXISTS createextension_02773_schema;
SET ROLE createextension_02773_create_user;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE EXTENSION。
-- primary-target-begin
CREATE EXTENSION "createextension_02773_MixedExt" WITH SCHEMA createextension_02773_schema VERSION 'createextension_02773_9.9.9' CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '22023' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS ext_available FROM pg_catalog.pg_available_extensions WHERE name = 'createextension_02773_MixedExt' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP EXTENSION IF EXISTS "createextension_02773_MixedExt" CASCADE;
DROP SCHEMA IF EXISTS createextension_02773_schema CASCADE;
DROP OWNED BY createextension_02773_create_user CASCADE;
DROP ROLE IF EXISTS createextension_02773_create_user;
