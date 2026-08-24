-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TABLE role_dependency=owner_role_not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTABLE01196
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|01196|owner_to|pg_constraint_query|DROP_TABLE_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS public.altertable_01196_tbl, altertable_01196_parent CASCADE;
DROP SCHEMA IF EXISTS altertable_01196_sch CASCADE;
DROP ROLE IF EXISTS altertable_01196_new_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altertable_01196_sch;
CREATE ROLE altertable_01196_new_owner LOGIN;
CREATE TABLE public.altertable_01196_tbl (altertable_01196_id integer PRIMARY KEY, altertable_01196_col integer, altertable_01196_txt text);
CREATE TABLE altertable_01196_parent (altertable_01196_id integer PRIMARY KEY, altertable_01196_col integer);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE altertable_01196_sch.altertable_01196_tbl OWNER TO altertable_01196_new_owner;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT c.conname, c.contype FROM pg_catalog.pg_constraint AS c WHERE c.conrelid = 'altertable_01196_tbl'::regclass ORDER BY c.conname;
-- 5. 清理全部本编号对象。
DROP SCHEMA IF EXISTS altertable_01196_sch CASCADE;
DROP OWNED BY altertable_01196_new_owner;
DROP ROLE IF EXISTS altertable_01196_new_owner;
DROP TABLE IF EXISTS public.altertable_01196_tbl, altertable_01196_parent CASCADE;
