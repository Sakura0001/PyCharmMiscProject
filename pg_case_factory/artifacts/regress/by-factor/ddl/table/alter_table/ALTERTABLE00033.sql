-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TABLE constraint_violation_existing_data=set_not_null_with_nulls
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTABLE00033
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALTERTABLE-SFV|sfv-01501cdaa35bd467a12a39ba|alter_column_set_drop_not_null
-- expected_outcome: expected_failure
-- expected_sqlstate: 23502
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altertable_00033_tbl, altertable_00033_parent CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE TABLE altertable_00033_tbl (altertable_00033_id integer PRIMARY KEY, altertable_00033_col integer, altertable_00033_txt text);
CREATE TABLE altertable_00033_parent (altertable_00033_id integer PRIMARY KEY, altertable_00033_col integer);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE altertable_00033_tbl ALTER COLUMN altertable_00033_col SET NOT NULL;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '23502' AS target_sqlstate_matches_expected;
SELECT count(*) AS table_exists FROM pg_catalog.pg_class WHERE relname = 'altertable_00033_tbl' AND relkind = 'r' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS altertable_00033_tbl, altertable_00033_parent CASCADE;
