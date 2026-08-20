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
-- case_id: ALTERTABLE02153
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|02153|rename_column|pg_attribute_query|DROP_TABLE_CASCADE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P07
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS public.altertable_02153_tbl, altertable_02153_parent CASCADE;
DROP SCHEMA IF EXISTS altertable_02153_sch CASCADE;
DROP ROLE IF EXISTS altertable_02153_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altertable_02153_sch;
CREATE ROLE altertable_02153_owner LOGIN;
GRANT USAGE ON SCHEMA public TO altertable_02153_owner;
CREATE TABLE public.altertable_02153_tbl (altertable_02153_id integer PRIMARY KEY, altertable_02153_col integer, altertable_02153_txt text);
CREATE TABLE altertable_02153_parent (altertable_02153_id integer PRIMARY KEY, altertable_02153_col integer);
ALTER TABLE public.altertable_02153_tbl OWNER TO altertable_02153_owner;
SET ROLE altertable_02153_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE IF EXISTS altertable_02153_sch.altertable_02153_tbl RENAME COLUMN altertable_02153_col TO "altertable_02153_Mixed New";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42P07' AS target_sqlstate_matches_expected;
SELECT a.attname, a.attnum FROM pg_catalog.pg_attribute AS a WHERE a.attrelid = 'altertable_02153_tbl'::regclass AND a.attnum > 0 ORDER BY a.attname;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS altertable_02153_sch CASCADE;
DROP OWNED BY altertable_02153_owner;
DROP ROLE IF EXISTS altertable_02153_owner;
DROP TABLE IF EXISTS public.altertable_02153_tbl, altertable_02153_parent CASCADE;
