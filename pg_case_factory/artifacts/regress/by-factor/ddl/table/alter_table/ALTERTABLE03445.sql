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
-- case_id: ALTERTABLE03445
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|03445|alter_column_type|SELECT_inspection|DROP_TABLE_CASCADE
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS public.altertable_03445_tbl, altertable_03445_parent CASCADE;
DROP SCHEMA IF EXISTS altertable_03445_sch CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altertable_03445_sch;
CREATE TABLE public.altertable_03445_tbl (altertable_03445_id integer PRIMARY KEY, altertable_03445_col integer, altertable_03445_txt text);
CREATE TABLE altertable_03445_parent (altertable_03445_id integer PRIMARY KEY, altertable_03445_col integer);
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE altertable_03445_sch.altertable_03445_tbl ALTER altertable_03445_col TYPE integer;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS row_count FROM altertable_03445_tbl ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP SCHEMA IF EXISTS altertable_03445_sch CASCADE;
DROP TABLE IF EXISTS public.altertable_03445_tbl, altertable_03445_parent CASCADE;
