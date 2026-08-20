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
-- case_id: ALTERTABLE04278
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|04278|alter_column_type|pg_constraint_query|ALTER_TABLE_REVERT
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS public.altertable_04278_tbl, altertable_04278_parent CASCADE;
DROP SCHEMA IF EXISTS altertable_04278_sch CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altertable_04278_sch;
CREATE TABLE public.altertable_04278_tbl (altertable_04278_id integer PRIMARY KEY, altertable_04278_col integer, altertable_04278_txt text);
CREATE TABLE altertable_04278_parent (altertable_04278_id integer PRIMARY KEY, altertable_04278_col integer);
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE altertable_04278_sch.altertable_04278_tbl ALTER altertable_04278_col TYPE integer;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT c.conname, c.contype FROM pg_catalog.pg_constraint AS c WHERE c.conrelid = 'altertable_04278_tbl'::regclass ORDER BY c.conname;
-- 5. 清理全部本编号对象。
DROP SCHEMA IF EXISTS altertable_04278_sch CASCADE;
DROP TABLE IF EXISTS public.altertable_04278_tbl, altertable_04278_parent CASCADE;
