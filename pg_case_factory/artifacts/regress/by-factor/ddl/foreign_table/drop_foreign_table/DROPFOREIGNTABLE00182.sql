-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP FOREIGN TABLE privilege_level=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPFOREIGNTABLE00182
-- source_md: skills/pg-sql-generation/references/statements/ddl/foreign_table/drop_foreign_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/foreign_table/drop_foreign_table.yaml
-- primary_obligation_id: DROPFOREIGNTABLE-EXT|00182|drop_foreign_table|error_assertion|recreate_fdw
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FOREIGN TABLE IF EXISTS dropforeigntable_00182_ft;
DROP SERVER IF EXISTS dropforeigntable_00182_server;
DROP OWNED BY dropforeigntable_00182_actor;
DROP ROLE IF EXISTS dropforeigntable_00182_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地外部表和因子专用夹具。
CREATE ROLE dropforeigntable_00182_actor LOGIN NOSUPERUSER;
CREATE EXTENSION IF NOT EXISTS file_fdw;
CREATE SERVER dropforeigntable_00182_server FOREIGN DATA WRAPPER file_fdw;
CREATE FOREIGN TABLE dropforeigntable_00182_ft (c integer) SERVER dropforeigntable_00182_server;
SET ROLE dropforeigntable_00182_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP FOREIGN TABLE。
-- primary-target-begin
DROP FOREIGN TABLE dropforeigntable_00182_ft CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS foreign_table_present FROM pg_catalog.pg_class WHERE relname = 'dropforeigntable_00182_ft' AND relkind = 'f' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FOREIGN TABLE IF EXISTS dropforeigntable_00182_ft;
DROP SERVER IF EXISTS dropforeigntable_00182_server;
DROP OWNED BY dropforeigntable_00182_actor;
DROP ROLE IF EXISTS dropforeigntable_00182_actor;
