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
-- case_id: ALTERTABLE02968
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|02968|rename_table|pg_class_catalog_query|DROP_TABLE_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P07
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altertable_02968_tbl, altertable_02968_parent CASCADE;
DROP ROLE IF EXISTS altertable_02968_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE ROLE altertable_02968_owner LOGIN;
GRANT USAGE ON SCHEMA public TO altertable_02968_owner;
CREATE TABLE altertable_02968_tbl (altertable_02968_id integer PRIMARY KEY, altertable_02968_col integer, altertable_02968_txt text);
CREATE TABLE altertable_02968_parent (altertable_02968_id integer PRIMARY KEY, altertable_02968_col integer);
ALTER TABLE altertable_02968_tbl OWNER TO altertable_02968_owner;
SET ROLE altertable_02968_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE IF EXISTS "altertable_02968_Mixed Table" RENAME TO altertable_02968_renamed;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42P07' AS target_sqlstate_matches_expected;
SELECT count(*) AS table_exists FROM pg_catalog.pg_class WHERE relname = 'altertable_02968_Mixed Table' AND relkind = 'r' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY altertable_02968_owner;
DROP ROLE IF EXISTS altertable_02968_owner;
DROP TABLE IF EXISTS altertable_02968_tbl, altertable_02968_parent CASCADE;
