-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE FOREIGN TABLE object_state=type_name_conflict
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEFOREIGNTABLE00897
-- source_md: skills/pg-sql-generation/references/statements/ddl/foreign_table/create_foreign_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/foreign_table/create_foreign_table.yaml
-- primary_obligation_id: CFT-EXT|00897|error_assertion|drop_foreign_table
-- expected_outcome: expected_failure
-- expected_sqlstate: 42710
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FOREIGN TABLE IF EXISTS createforeigntable_00897_ft CASCADE;
DROP SERVER IF EXISTS createforeigntable_00897_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS createforeigntable_00897_fdw CASCADE;
DROP TYPE IF EXISTS createforeigntable_00897_ft CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE FOREIGN DATA WRAPPER createforeigntable_00897_fdw;
CREATE SERVER createforeigntable_00897_server FOREIGN DATA WRAPPER createforeigntable_00897_fdw;
CREATE TYPE createforeigntable_00897_ft AS (createforeigntable_00897_val integer);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE FOREIGN TABLE。
-- primary-target-begin
CREATE FOREIGN TABLE createforeigntable_00897_ft (createforeigntable_00897_col integer GENERATED ALWAYS AS (1) VIRTUAL NOT ENFORCED) SERVER createforeigntable_00897_server;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42710' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP FOREIGN TABLE IF EXISTS createforeigntable_00897_ft CASCADE;
DROP TYPE IF EXISTS createforeigntable_00897_ft CASCADE;
DROP SERVER IF EXISTS createforeigntable_00897_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS createforeigntable_00897_fdw CASCADE;
