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
-- case_id: ALTERTABLE02871
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|02871|rename_table|pg_class_catalog_query|RESET_STATE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P07
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS public.altertable_02871_tbl, altertable_02871_parent CASCADE;
DROP SCHEMA IF EXISTS altertable_02871_sch CASCADE;
DROP ROLE IF EXISTS altertable_02871_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altertable_02871_sch;
CREATE ROLE altertable_02871_owner LOGIN;
GRANT USAGE ON SCHEMA public TO altertable_02871_owner;
CREATE TABLE public.altertable_02871_tbl (altertable_02871_id integer PRIMARY KEY, altertable_02871_col integer, altertable_02871_txt text);
CREATE TABLE altertable_02871_parent (altertable_02871_id integer PRIMARY KEY, altertable_02871_col integer);
ALTER TABLE public.altertable_02871_tbl OWNER TO altertable_02871_owner;
SET ROLE altertable_02871_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE IF EXISTS altertable_02871_sch.altertable_02871_tbl RENAME TO "altertable_02871_Mixed New";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42P07' AS target_sqlstate_matches_expected;
SELECT count(*) AS table_exists FROM pg_catalog.pg_class WHERE relname = 'altertable_02871_tbl' AND relkind = 'r' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS altertable_02871_sch CASCADE;
DROP OWNED BY altertable_02871_owner;
DROP ROLE IF EXISTS altertable_02871_owner;
DROP TABLE IF EXISTS public.altertable_02871_tbl, altertable_02871_parent CASCADE;
