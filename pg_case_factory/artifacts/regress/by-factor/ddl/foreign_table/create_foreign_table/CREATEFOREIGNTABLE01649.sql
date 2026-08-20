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
-- case_id: CREATEFOREIGNTABLE01649
-- source_md: skills/pg-sql-generation/references/statements/ddl/foreign_table/create_foreign_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/foreign_table/create_foreign_table.yaml
-- primary_obligation_id: CFT-EXT|01649|error_assertion|drop_server
-- expected_outcome: expected_failure
-- expected_sqlstate: 42710
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createforeigntable_01649_parent1 CASCADE;
DROP FOREIGN TABLE IF EXISTS createforeigntable_01649_ft CASCADE;
DROP SERVER IF EXISTS createforeigntable_01649_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS createforeigntable_01649_fdw CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE FOREIGN DATA WRAPPER createforeigntable_01649_fdw;
CREATE SERVER createforeigntable_01649_server FOREIGN DATA WRAPPER createforeigntable_01649_fdw;
CREATE TABLE createforeigntable_01649_parent1 (createforeigntable_01649_col integer);
CREATE FOREIGN TABLE createforeigntable_01649_ft () SERVER createforeigntable_01649_server;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE FOREIGN TABLE。
-- primary-target-begin
CREATE FOREIGN TABLE createforeigntable_01649_ft (createforeigntable_01649_col jsonb) INHERITS (createforeigntable_01649_parent1) SERVER createforeigntable_01649_server;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42710' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP FOREIGN TABLE IF EXISTS createforeigntable_01649_ft CASCADE;
DROP SERVER IF EXISTS createforeigntable_01649_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS createforeigntable_01649_fdw CASCADE;
DROP TABLE IF EXISTS createforeigntable_01649_parent1 CASCADE;
