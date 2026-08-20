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
-- case_id: ALTERTABLE03997
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|03997|add_column|pg_constraint_query|DROP_TABLE_CASCADE
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS public.altertable_03997_tbl, altertable_03997_parent CASCADE;
DROP SCHEMA IF EXISTS altertable_03997_sch CASCADE;
DROP ROLE IF EXISTS altertable_03997_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altertable_03997_sch;
CREATE ROLE altertable_03997_owner LOGIN;
GRANT USAGE ON SCHEMA public TO altertable_03997_owner;
CREATE TABLE public.altertable_03997_tbl (altertable_03997_id integer PRIMARY KEY, altertable_03997_col integer, altertable_03997_txt text);
CREATE TABLE altertable_03997_parent (altertable_03997_id integer PRIMARY KEY, altertable_03997_col integer);
ALTER TABLE public.altertable_03997_tbl OWNER TO altertable_03997_owner;
SET ROLE altertable_03997_owner;
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE IF EXISTS altertable_03997_sch.altertable_03997_tbl ADD altertable_03997_col integer;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT c.conname, c.contype FROM pg_catalog.pg_constraint AS c WHERE c.conrelid = 'altertable_03997_tbl'::regclass ORDER BY c.conname;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS altertable_03997_sch CASCADE;
DROP OWNED BY altertable_03997_owner;
DROP ROLE IF EXISTS altertable_03997_owner;
DROP TABLE IF EXISTS public.altertable_03997_tbl, altertable_03997_parent CASCADE;
