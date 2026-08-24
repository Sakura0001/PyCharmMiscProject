-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : IMPORT FOREIGN SCHEMA remote_schema_name_shape=simple_id
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: IMPORTFOREIGNSCHEMA00039
-- source_md: skills/pg-sql-generation/references/statements/ddl/foreign_schema/import_foreign_schema.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/foreign_schema/import_foreign_schema.yaml
-- primary_obligation_id: IMPORTFOREIGNSCHEMA-SFV|sfv-608ea86de6f025688c69d4a2|import_foreign_schema_statement
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SCHEMA IF EXISTS importforeignschema_00039_lschema CASCADE;
DROP SERVER IF EXISTS importforeignschema_00039_srv;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE EXTENSION IF NOT EXISTS file_fdw;
CREATE SERVER importforeignschema_00039_srv FOREIGN DATA WRAPPER file_fdw;
CREATE SCHEMA importforeignschema_00039_lschema;
CREATE FOREIGN TABLE importforeignschema_00039_lschema.importforeignschema_00039_ft (c1 text) SERVER importforeignschema_00039_srv OPTIONS (filename '/tmp/pgcf_importfs_fixture.csv');
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 IMPORT FOREIGN SCHEMA。
-- primary-target-begin
IMPORT FOREIGN SCHEMA importforeignschema_00039_remote FROM SERVER importforeignschema_00039_srv INTO importforeignschema_00039_lschema;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS foreign_tables_present FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid WHERE n.nspname = 'importforeignschema_00039_lschema' AND c.relname = 'importforeignschema_00039_ft' AND c.relkind = 'f' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP FOREIGN TABLE IF EXISTS importforeignschema_00039_lschema.importforeignschema_00039_ft;
DROP SCHEMA IF EXISTS importforeignschema_00039_lschema CASCADE;
DROP SERVER IF EXISTS importforeignschema_00039_srv;
