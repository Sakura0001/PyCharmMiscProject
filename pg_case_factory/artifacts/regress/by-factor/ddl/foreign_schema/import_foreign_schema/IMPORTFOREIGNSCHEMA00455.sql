-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : IMPORT FOREIGN SCHEMA no_create_privilege=lacks_create
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: IMPORTFOREIGNSCHEMA00455
-- source_md: skills/pg-sql-generation/references/statements/ddl/foreign_schema/import_foreign_schema.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/foreign_schema/import_foreign_schema.yaml
-- primary_obligation_id: IMPORTFOREIGNSCHEMA-EXT|00455|error_assertion|drop_server|privilege_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
RESET ROLE;
DROP SCHEMA IF EXISTS importforeignschema_00455_lschema CASCADE;
DROP SERVER IF EXISTS importforeignschema_00455_srv;
DROP ROLE IF EXISTS importforeignschema_00455_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE EXTENSION IF NOT EXISTS file_fdw;
CREATE SERVER importforeignschema_00455_srv FOREIGN DATA WRAPPER file_fdw;
CREATE ROLE importforeignschema_00455_actor LOGIN NOSUPERUSER;
GRANT USAGE ON FOREIGN SERVER importforeignschema_00455_srv TO importforeignschema_00455_actor;
CREATE SCHEMA importforeignschema_00455_lschema;
SELECT 1 AS target_foreign_table_intentionally_absent;
SET ROLE importforeignschema_00455_actor;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 IMPORT FOREIGN SCHEMA。
-- primary-target-begin
IMPORT FOREIGN SCHEMA importforeignschema_00455_remote FROM SERVER importforeignschema_00455_srv INTO importforeignschema_00455_lschema;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SERVER IF EXISTS importforeignschema_00455_srv;
DROP SCHEMA IF EXISTS importforeignschema_00455_lschema CASCADE;
DROP ROLE IF EXISTS importforeignschema_00455_actor;
