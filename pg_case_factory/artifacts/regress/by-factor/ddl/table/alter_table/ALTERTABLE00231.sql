-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TABLE privilege_level=non_owner_no_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTABLE00231
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|00231|drop_column|pg_class_catalog_query|RESET_STATE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS public.altertable_00231_tbl, altertable_00231_parent CASCADE;
DROP SCHEMA IF EXISTS altertable_00231_sch CASCADE;
DROP ROLE IF EXISTS altertable_00231_owner;
DROP ROLE IF EXISTS altertable_00231_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altertable_00231_sch;
CREATE ROLE altertable_00231_owner LOGIN;
CREATE ROLE altertable_00231_actor LOGIN;
GRANT USAGE ON SCHEMA public TO altertable_00231_owner;
GRANT USAGE ON SCHEMA public TO altertable_00231_actor;
CREATE TABLE public.altertable_00231_tbl (altertable_00231_id integer PRIMARY KEY, altertable_00231_col integer, altertable_00231_txt text);
CREATE TABLE altertable_00231_parent (altertable_00231_id integer PRIMARY KEY, altertable_00231_col integer);
ALTER TABLE public.altertable_00231_tbl OWNER TO altertable_00231_owner;
SET ROLE altertable_00231_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE altertable_00231_sch.altertable_00231_tbl DROP altertable_00231_col;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) AS table_exists FROM pg_catalog.pg_class WHERE relname = 'altertable_00231_tbl' AND relkind = 'r' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS altertable_00231_sch CASCADE;
DROP OWNED BY altertable_00231_owner;
DROP ROLE IF EXISTS altertable_00231_owner;
DROP OWNED BY altertable_00231_actor;
DROP ROLE IF EXISTS altertable_00231_actor;
DROP TABLE IF EXISTS public.altertable_00231_tbl, altertable_00231_parent CASCADE;
