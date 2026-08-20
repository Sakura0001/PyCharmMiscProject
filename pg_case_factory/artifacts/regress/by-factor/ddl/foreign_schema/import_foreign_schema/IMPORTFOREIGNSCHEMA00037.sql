-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : IMPORT FOREIGN SCHEMA privilege_level=usage_and_create
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: IMPORTFOREIGNSCHEMA00037
-- source_md: skills/pg-sql-generation/references/statements/ddl/foreign_schema/import_foreign_schema.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/foreign_schema/import_foreign_schema.yaml
-- primary_obligation_id: IMPORTFOREIGNSCHEMA-SFV|sfv-bb544fdfb6a7a06baaa7db8b|import_foreign_schema_usage_and_create
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
RESET ROLE;
DROP SCHEMA IF EXISTS importforeignschema_00037_lschema CASCADE;
DROP SERVER IF EXISTS importforeignschema_00037_srv;
DROP ROLE IF EXISTS importforeignschema_00037_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE EXTENSION IF NOT EXISTS file_fdw;
CREATE SERVER importforeignschema_00037_srv FOREIGN DATA WRAPPER file_fdw;
CREATE ROLE importforeignschema_00037_actor LOGIN NOSUPERUSER;
GRANT USAGE ON FOREIGN SERVER importforeignschema_00037_srv TO importforeignschema_00037_actor;
GRANT CREATE ON SCHEMA importforeignschema_00037_lschema TO importforeignschema_00037_actor;
CREATE SCHEMA importforeignschema_00037_lschema;
CREATE FOREIGN TABLE importforeignschema_00037_lschema.importforeignschema_00037_ft (c1 text) SERVER importforeignschema_00037_srv OPTIONS (filename '/tmp/pgcf_importfs_fixture.csv');
SET ROLE importforeignschema_00037_actor;
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 IMPORT FOREIGN SCHEMA。
-- primary-target-begin
IMPORT FOREIGN SCHEMA importforeignschema_00037_remote FROM SERVER importforeignschema_00037_srv INTO importforeignschema_00037_lschema;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS foreign_tables_present FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid WHERE n.nspname = 'importforeignschema_00037_lschema' AND c.relname = 'importforeignschema_00037_ft' AND c.relkind = 'f' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FOREIGN TABLE IF EXISTS importforeignschema_00037_lschema.importforeignschema_00037_ft;
DROP SCHEMA IF EXISTS importforeignschema_00037_lschema CASCADE;
DROP SERVER IF EXISTS importforeignschema_00037_srv;
DROP ROLE IF EXISTS importforeignschema_00037_actor;
