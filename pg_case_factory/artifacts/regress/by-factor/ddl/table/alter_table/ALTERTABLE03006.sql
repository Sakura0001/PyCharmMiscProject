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
-- case_id: ALTERTABLE03006
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|03006|rename_table|SELECT_inspection|ALTER_TABLE_REVERT
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P07
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS public.altertable_03006_tbl, altertable_03006_parent CASCADE;
DROP SCHEMA IF EXISTS altertable_03006_sch CASCADE;
DROP ROLE IF EXISTS altertable_03006_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altertable_03006_sch;
CREATE ROLE altertable_03006_owner LOGIN;
GRANT USAGE ON SCHEMA public TO altertable_03006_owner;
CREATE TABLE public.altertable_03006_tbl (altertable_03006_id integer PRIMARY KEY, altertable_03006_col integer, altertable_03006_txt text);
CREATE TABLE altertable_03006_parent (altertable_03006_id integer PRIMARY KEY, altertable_03006_col integer);
ALTER TABLE public.altertable_03006_tbl OWNER TO altertable_03006_owner;
SET ROLE altertable_03006_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE IF EXISTS altertable_03006_sch.altertable_03006_tbl RENAME TO altertable_03006_renamed;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42P07' AS target_sqlstate_matches_expected;
SELECT count(*) AS row_count FROM altertable_03006_tbl ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS altertable_03006_sch CASCADE;
DROP OWNED BY altertable_03006_owner;
DROP ROLE IF EXISTS altertable_03006_owner;
DROP TABLE IF EXISTS public.altertable_03006_tbl, altertable_03006_parent CASCADE;
