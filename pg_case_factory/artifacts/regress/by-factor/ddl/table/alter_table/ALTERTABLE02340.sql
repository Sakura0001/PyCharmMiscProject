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
-- case_id: ALTERTABLE02340
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|02340|rename_table|information_schema_query|DROP_TABLE_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P07
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS public.altertable_02340_tbl, altertable_02340_parent CASCADE;
DROP SCHEMA IF EXISTS altertable_02340_sch CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altertable_02340_sch;
CREATE TABLE public.altertable_02340_tbl (altertable_02340_id integer PRIMARY KEY, altertable_02340_col integer, altertable_02340_txt text);
CREATE TABLE altertable_02340_parent (altertable_02340_id integer PRIMARY KEY, altertable_02340_col integer);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE altertable_02340_sch.altertable_02340_tbl RENAME TO altertable_02340_tbl;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42P07' AS target_sqlstate_matches_expected;
SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'altertable_02340_tbl' ORDER BY column_name;
-- 5. 清理全部本编号对象。
DROP SCHEMA IF EXISTS altertable_02340_sch CASCADE;
DROP TABLE IF EXISTS public.altertable_02340_tbl, altertable_02340_parent CASCADE;
