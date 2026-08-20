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
-- case_id: ALTERTABLE00533
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|00533|drop_column|pg_attribute_query|DROP_TABLE_CASCADE
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS public.altertable_00533_tbl, altertable_00533_parent CASCADE;
DROP SCHEMA IF EXISTS altertable_00533_sch CASCADE;
DROP ROLE IF EXISTS altertable_00533_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altertable_00533_sch;
CREATE ROLE altertable_00533_owner LOGIN;
GRANT USAGE ON SCHEMA public TO altertable_00533_owner;
CREATE TABLE public.altertable_00533_tbl (altertable_00533_id integer PRIMARY KEY, altertable_00533_col integer, altertable_00533_txt text);
CREATE TABLE altertable_00533_parent (altertable_00533_id integer PRIMARY KEY, altertable_00533_col integer);
ALTER TABLE public.altertable_00533_tbl OWNER TO altertable_00533_owner;
SET ROLE altertable_00533_owner;
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE IF EXISTS altertable_00533_sch.altertable_00533_tbl DROP altertable_00533_col;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT a.attname, a.attnum FROM pg_catalog.pg_attribute AS a WHERE a.attrelid = 'altertable_00533_tbl'::regclass AND a.attnum > 0 ORDER BY a.attname;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS altertable_00533_sch CASCADE;
DROP OWNED BY altertable_00533_owner;
DROP ROLE IF EXISTS altertable_00533_owner;
DROP TABLE IF EXISTS public.altertable_00533_tbl, altertable_00533_parent CASCADE;
