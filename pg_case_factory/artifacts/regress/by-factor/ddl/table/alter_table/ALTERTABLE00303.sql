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
-- case_id: ALTERTABLE00303
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|00303|drop_column|information_schema_query|RESET_STATE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS public.altertable_00303_tbl, altertable_00303_parent CASCADE;
DROP SCHEMA IF EXISTS altertable_00303_sch CASCADE;
DROP ROLE IF EXISTS altertable_00303_owner;
DROP ROLE IF EXISTS altertable_00303_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altertable_00303_sch;
CREATE ROLE altertable_00303_owner LOGIN;
CREATE ROLE altertable_00303_actor LOGIN;
GRANT USAGE ON SCHEMA public TO altertable_00303_owner;
GRANT USAGE ON SCHEMA public TO altertable_00303_actor;
CREATE TABLE public.altertable_00303_tbl (altertable_00303_id integer PRIMARY KEY, altertable_00303_col integer, altertable_00303_txt text);
CREATE TABLE altertable_00303_parent (altertable_00303_id integer PRIMARY KEY, altertable_00303_col integer);
ALTER TABLE public.altertable_00303_tbl OWNER TO altertable_00303_owner;
SET ROLE altertable_00303_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE IF EXISTS altertable_00303_sch.altertable_00303_tbl DROP altertable_00303_col;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'altertable_00303_tbl' ORDER BY column_name;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS altertable_00303_sch CASCADE;
DROP OWNED BY altertable_00303_owner;
DROP ROLE IF EXISTS altertable_00303_owner;
DROP OWNED BY altertable_00303_actor;
DROP ROLE IF EXISTS altertable_00303_actor;
DROP TABLE IF EXISTS public.altertable_00303_tbl, altertable_00303_parent CASCADE;
