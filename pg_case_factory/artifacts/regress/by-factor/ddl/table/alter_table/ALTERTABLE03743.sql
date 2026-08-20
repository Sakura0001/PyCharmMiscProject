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
-- case_id: ALTERTABLE03743
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|03743|add_column|information_schema_query|RESET_STATE
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS public.altertable_03743_tbl, altertable_03743_parent CASCADE;
DROP SCHEMA IF EXISTS altertable_03743_sch CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altertable_03743_sch;
CREATE TABLE public.altertable_03743_tbl (altertable_03743_id integer PRIMARY KEY, altertable_03743_col integer, altertable_03743_txt text);
CREATE TABLE altertable_03743_parent (altertable_03743_id integer PRIMARY KEY, altertable_03743_col integer);
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE altertable_03743_sch.altertable_03743_tbl ADD altertable_03743_col integer;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'altertable_03743_tbl' ORDER BY column_name;
-- 5. 清理全部本编号对象。
DROP SCHEMA IF EXISTS altertable_03743_sch CASCADE;
DROP TABLE IF EXISTS public.altertable_03743_tbl, altertable_03743_parent CASCADE;
