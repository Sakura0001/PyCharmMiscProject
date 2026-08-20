-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TABLE schema_dependency=schema_not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTABLE03279
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|03279|set_schema|pg_constraint_query|RESET_STATE
-- expected_outcome: expected_failure
-- expected_sqlstate: 3F000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS public.altertable_03279_tbl, altertable_03279_parent CASCADE;
DROP SCHEMA IF EXISTS altertable_03279_sch CASCADE;
DROP ROLE IF EXISTS altertable_03279_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altertable_03279_sch;
CREATE ROLE altertable_03279_owner LOGIN;
GRANT USAGE ON SCHEMA public TO altertable_03279_owner;
CREATE TABLE public.altertable_03279_tbl (altertable_03279_id integer PRIMARY KEY, altertable_03279_col integer, altertable_03279_txt text);
CREATE TABLE altertable_03279_parent (altertable_03279_id integer PRIMARY KEY, altertable_03279_col integer);
ALTER TABLE public.altertable_03279_tbl OWNER TO altertable_03279_owner;
SET ROLE altertable_03279_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE IF EXISTS altertable_03279_sch.altertable_03279_tbl SET SCHEMA altertable_03279_new_sch;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '3F000' AS target_sqlstate_matches_expected;
SELECT c.conname, c.contype FROM pg_catalog.pg_constraint AS c WHERE c.conrelid = 'altertable_03279_tbl'::regclass ORDER BY c.conname;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS altertable_03279_sch CASCADE;
DROP OWNED BY altertable_03279_owner;
DROP ROLE IF EXISTS altertable_03279_owner;
DROP TABLE IF EXISTS public.altertable_03279_tbl, altertable_03279_parent CASCADE;
