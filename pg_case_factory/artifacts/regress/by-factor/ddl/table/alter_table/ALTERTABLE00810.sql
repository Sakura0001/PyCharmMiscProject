-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TABLE object_state=exists_normal
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTABLE00810
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|00810|drop_column|pg_class_catalog_query|ALTER_TABLE_REVERT
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altertable_00810_tbl, altertable_00810_parent CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE TABLE altertable_00810_tbl (altertable_00810_id integer PRIMARY KEY, altertable_00810_col integer, altertable_00810_txt text);
CREATE TABLE altertable_00810_parent (altertable_00810_id integer PRIMARY KEY, altertable_00810_col integer);
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE IF EXISTS "altertable_00810_Mixed Table" DROP altertable_00810_col;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS table_exists FROM pg_catalog.pg_class WHERE relname = 'altertable_00810_Mixed Table' AND relkind = 'r' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS altertable_00810_tbl, altertable_00810_parent CASCADE;
