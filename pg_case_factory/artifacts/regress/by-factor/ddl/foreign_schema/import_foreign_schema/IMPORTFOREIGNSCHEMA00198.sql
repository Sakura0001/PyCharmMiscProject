-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : IMPORT FOREIGN SCHEMA server_existence=server_not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: IMPORTFOREIGNSCHEMA00198
-- source_md: skills/pg-sql-generation/references/statements/ddl/foreign_schema/import_foreign_schema.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/foreign_schema/import_foreign_schema.yaml
-- primary_obligation_id: IMPORTFOREIGNSCHEMA-EXT|00198|error_assertion|drop_foreign_tables|server_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SCHEMA IF EXISTS importforeignschema_00198_lschema CASCADE;
DROP SERVER IF EXISTS importforeignschema_00198_srv;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE EXTENSION IF NOT EXISTS file_fdw;
CREATE SCHEMA importforeignschema_00198_lschema;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 IMPORT FOREIGN SCHEMA。
-- primary-target-begin
IMPORT FOREIGN SCHEMA importforeignschema_00198_remote EXCEPT (importforeignschema_00198_ft) FROM SERVER importforeignschema_00198_nosrv INTO importforeignschema_00198_lschema OPTIONS (import_force_not_null 'true');
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP FOREIGN TABLE IF EXISTS importforeignschema_00198_lschema.importforeignschema_00198_ft;
DROP SCHEMA IF EXISTS importforeignschema_00198_lschema CASCADE;
