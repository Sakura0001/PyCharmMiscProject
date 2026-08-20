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
-- case_id: ALTERTABLE03321
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|03321|set_schema|information_schema_query|DROP_TABLE_CASCADE
-- expected_outcome: expected_failure
-- expected_sqlstate: 3F000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS public.altertable_03321_tbl, altertable_03321_parent CASCADE;
DROP SCHEMA IF EXISTS altertable_03321_new_sch CASCADE;
DROP SCHEMA IF EXISTS altertable_03321_sch CASCADE;
DROP ROLE IF EXISTS altertable_03321_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altertable_03321_new_sch;
CREATE SCHEMA IF NOT EXISTS altertable_03321_sch;
CREATE ROLE altertable_03321_owner LOGIN;
GRANT USAGE ON SCHEMA public TO altertable_03321_owner;
CREATE TABLE public.altertable_03321_tbl (altertable_03321_id integer PRIMARY KEY, altertable_03321_col integer, altertable_03321_txt text);
CREATE TABLE altertable_03321_parent (altertable_03321_id integer PRIMARY KEY, altertable_03321_col integer);
ALTER TABLE public.altertable_03321_tbl OWNER TO altertable_03321_owner;
SET ROLE altertable_03321_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE IF EXISTS altertable_03321_sch.altertable_03321_tbl SET SCHEMA altertable_03321_no_such_sch;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '3F000' AS target_sqlstate_matches_expected;
SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'altertable_03321_tbl' ORDER BY column_name;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS altertable_03321_new_sch CASCADE;
DROP SCHEMA IF EXISTS altertable_03321_sch CASCADE;
DROP OWNED BY altertable_03321_owner;
DROP ROLE IF EXISTS altertable_03321_owner;
DROP TABLE IF EXISTS public.altertable_03321_tbl, altertable_03321_parent CASCADE;
