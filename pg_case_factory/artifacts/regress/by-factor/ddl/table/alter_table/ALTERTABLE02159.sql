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
-- case_id: ALTERTABLE02159
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|02159|rename_column|pg_constraint_query|RESET_STATE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P07
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS public.altertable_02159_tbl, altertable_02159_parent CASCADE;
DROP SCHEMA IF EXISTS altertable_02159_sch CASCADE;
DROP ROLE IF EXISTS altertable_02159_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altertable_02159_sch;
CREATE ROLE altertable_02159_owner LOGIN;
GRANT USAGE ON SCHEMA public TO altertable_02159_owner;
CREATE TABLE public.altertable_02159_tbl (altertable_02159_id integer PRIMARY KEY, altertable_02159_col integer, altertable_02159_txt text);
CREATE TABLE altertable_02159_parent (altertable_02159_id integer PRIMARY KEY, altertable_02159_col integer);
ALTER TABLE public.altertable_02159_tbl OWNER TO altertable_02159_owner;
SET ROLE altertable_02159_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE IF EXISTS altertable_02159_sch.altertable_02159_tbl RENAME COLUMN altertable_02159_col TO "altertable_02159_Mixed New";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42P07' AS target_sqlstate_matches_expected;
SELECT c.conname, c.contype FROM pg_catalog.pg_constraint AS c WHERE c.conrelid = 'altertable_02159_tbl'::regclass ORDER BY c.conname;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS altertable_02159_sch CASCADE;
DROP OWNED BY altertable_02159_owner;
DROP ROLE IF EXISTS altertable_02159_owner;
DROP TABLE IF EXISTS public.altertable_02159_tbl, altertable_02159_parent CASCADE;
