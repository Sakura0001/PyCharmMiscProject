-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TABLE new_name_shape=duplicate
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTABLE01880
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|01880|rename_column|information_schema_query|DROP_TABLE_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P07
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altertable_01880_tbl, altertable_01880_parent CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE TABLE altertable_01880_tbl (altertable_01880_id integer PRIMARY KEY, altertable_01880_col integer, altertable_01880_txt text);
CREATE TABLE altertable_01880_parent (altertable_01880_id integer PRIMARY KEY, altertable_01880_col integer);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE altertable_01880_tbl RENAME COLUMN altertable_01880_col TO altertable_01880_renamed;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42P07' AS target_sqlstate_matches_expected;
SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'altertable_01880_tbl' ORDER BY column_name;
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS altertable_01880_tbl, altertable_01880_parent CASCADE;
