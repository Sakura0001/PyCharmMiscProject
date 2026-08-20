-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : IMPORT FOREIGN SCHEMA local_schema_name_shape=nonexistent_schema
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: IMPORTFOREIGNSCHEMA00300
-- source_md: skills/pg-sql-generation/references/statements/ddl/foreign_schema/import_foreign_schema.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/foreign_schema/import_foreign_schema.yaml
-- primary_obligation_id: IMPORTFOREIGNSCHEMA-EXT|00300|pg_class_catalog_query|drop_schema|schema_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 3F001
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SCHEMA IF EXISTS importforeignschema_00300_noschema CASCADE;
DROP SERVER IF EXISTS importforeignschema_00300_srv;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE EXTENSION IF NOT EXISTS file_fdw;
CREATE SERVER importforeignschema_00300_srv FOREIGN DATA WRAPPER file_fdw;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 IMPORT FOREIGN SCHEMA。
-- primary-target-begin
IMPORT FOREIGN SCHEMA importforeignschema_00300_remote LIMIT TO (importforeignschema_00300_ft) FROM SERVER importforeignschema_00300_srv INTO importforeignschema_00300_noschema;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '3F001' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS foreign_tables_absent FROM pg_catalog.pg_class c JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid WHERE n.nspname = 'importforeignschema_00300_noschema' AND c.relname = 'importforeignschema_00300_ft' AND c.relkind = 'f' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP SCHEMA IF EXISTS importforeignschema_00300_noschema CASCADE;
DROP SERVER IF EXISTS importforeignschema_00300_srv;
