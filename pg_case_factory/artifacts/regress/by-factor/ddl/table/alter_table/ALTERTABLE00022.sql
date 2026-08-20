-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TABLE column_name_shape=reserved_word
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTABLE00022
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALTERTABLE-SFV|sfv-b92f95c98b77f867d1d02992|alter_column_type
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altertable_00022_tbl, altertable_00022_parent CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE TABLE altertable_00022_tbl (altertable_00022_id integer PRIMARY KEY, altertable_00022_col integer, altertable_00022_txt text);
CREATE TABLE altertable_00022_parent (altertable_00022_id integer PRIMARY KEY, altertable_00022_col integer);
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE altertable_00022_tbl ALTER "altertable_00022_user" TYPE integer;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS table_exists FROM pg_catalog.pg_class WHERE relname = 'altertable_00022_tbl' AND relkind = 'r' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS altertable_00022_tbl, altertable_00022_parent CASCADE;
