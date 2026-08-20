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
-- case_id: ALTERTABLE00721
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|00721|drop_column|information_schema_query|DROP_TABLE_CASCADE
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS public.altertable_00721_tbl, altertable_00721_parent CASCADE;
DROP SCHEMA IF EXISTS altertable_00721_sch CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altertable_00721_sch;
CREATE TABLE public.altertable_00721_tbl (altertable_00721_id integer PRIMARY KEY, altertable_00721_col integer, altertable_00721_txt text);
CREATE TABLE altertable_00721_parent (altertable_00721_id integer PRIMARY KEY, altertable_00721_col integer);
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE altertable_00721_sch.altertable_00721_tbl DROP altertable_00721_col;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'altertable_00721_tbl' ORDER BY column_name;
-- 5. 清理全部本编号对象。
DROP SCHEMA IF EXISTS altertable_00721_sch CASCADE;
DROP TABLE IF EXISTS public.altertable_00721_tbl, altertable_00721_parent CASCADE;
