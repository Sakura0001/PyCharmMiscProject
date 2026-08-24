-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE FOREIGN TABLE object_state=already_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEFOREIGNTABLE02191
-- source_md: skills/pg-sql-generation/references/statements/ddl/foreign_table/create_foreign_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/foreign_table/create_foreign_table.yaml
-- primary_obligation_id: CFT-EXT|02191|error_assertion|drop_parent_table
-- expected_outcome: expected_failure
-- expected_sqlstate: 42710
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createforeigntable_02191_parent1 CASCADE;
DROP FOREIGN TABLE IF EXISTS createforeigntable_02191_ft CASCADE;
DROP SERVER IF EXISTS createforeigntable_02191_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS createforeigntable_02191_fdw CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE FOREIGN DATA WRAPPER createforeigntable_02191_fdw;
CREATE SERVER createforeigntable_02191_server FOREIGN DATA WRAPPER createforeigntable_02191_fdw;
CREATE TABLE createforeigntable_02191_parent1 (createforeigntable_02191_col integer);
CREATE FOREIGN TABLE createforeigntable_02191_ft () SERVER createforeigntable_02191_server;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE FOREIGN TABLE。
-- primary-target-begin
CREATE FOREIGN TABLE createforeigntable_02191_ft (createforeigntable_02191_col timestamp) INHERITS (createforeigntable_02191_parent1) SERVER createforeigntable_02191_server;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42710' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP FOREIGN TABLE IF EXISTS createforeigntable_02191_ft CASCADE;
DROP SERVER IF EXISTS createforeigntable_02191_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS createforeigntable_02191_fdw CASCADE;
DROP TABLE IF EXISTS createforeigntable_02191_parent1 CASCADE;
