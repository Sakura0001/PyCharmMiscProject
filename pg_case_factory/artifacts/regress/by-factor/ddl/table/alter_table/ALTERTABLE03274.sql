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
-- case_id: ALTERTABLE03274
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|03274|set_schema|pg_attribute_query|ALTER_TABLE_REVERT
-- expected_outcome: expected_failure
-- expected_sqlstate: 3F000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS public.altertable_03274_tbl, altertable_03274_parent CASCADE;
DROP SCHEMA IF EXISTS altertable_03274_sch CASCADE;
DROP ROLE IF EXISTS altertable_03274_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altertable_03274_sch;
CREATE ROLE altertable_03274_owner LOGIN;
GRANT USAGE ON SCHEMA public TO altertable_03274_owner;
CREATE TABLE public.altertable_03274_tbl (altertable_03274_id integer PRIMARY KEY, altertable_03274_col integer, altertable_03274_txt text);
CREATE TABLE altertable_03274_parent (altertable_03274_id integer PRIMARY KEY, altertable_03274_col integer);
ALTER TABLE public.altertable_03274_tbl OWNER TO altertable_03274_owner;
SET ROLE altertable_03274_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE IF EXISTS altertable_03274_sch.altertable_03274_tbl SET SCHEMA altertable_03274_new_sch;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '3F000' AS target_sqlstate_matches_expected;
SELECT a.attname, a.attnum FROM pg_catalog.pg_attribute AS a WHERE a.attrelid = 'altertable_03274_tbl'::regclass AND a.attnum > 0 ORDER BY a.attname;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS altertable_03274_sch CASCADE;
DROP OWNED BY altertable_03274_owner;
DROP ROLE IF EXISTS altertable_03274_owner;
DROP TABLE IF EXISTS public.altertable_03274_tbl, altertable_03274_parent CASCADE;
