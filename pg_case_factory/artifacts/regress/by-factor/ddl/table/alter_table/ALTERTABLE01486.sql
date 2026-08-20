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
-- case_id: ALTERTABLE01486
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|01486|drop_column|SELECT_inspection|ALTER_TABLE_REVERT
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS public.altertable_01486_tbl, altertable_01486_parent CASCADE;
DROP SCHEMA IF EXISTS altertable_01486_sch CASCADE;
DROP ROLE IF EXISTS altertable_01486_owner;
DROP ROLE IF EXISTS altertable_01486_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altertable_01486_sch;
CREATE ROLE altertable_01486_owner LOGIN;
CREATE ROLE altertable_01486_actor LOGIN;
GRANT USAGE ON SCHEMA public TO altertable_01486_owner;
GRANT USAGE ON SCHEMA public TO altertable_01486_actor;
CREATE TABLE public.altertable_01486_tbl (altertable_01486_id integer PRIMARY KEY, altertable_01486_col integer, altertable_01486_txt text);
CREATE TABLE altertable_01486_parent (altertable_01486_id integer PRIMARY KEY, altertable_01486_col integer);
ALTER TABLE public.altertable_01486_tbl OWNER TO altertable_01486_owner;
SET ROLE altertable_01486_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE IF EXISTS altertable_01486_sch.altertable_01486_tbl DROP altertable_01486_col;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) AS row_count FROM altertable_01486_tbl ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS altertable_01486_sch CASCADE;
DROP OWNED BY altertable_01486_owner;
DROP ROLE IF EXISTS altertable_01486_owner;
DROP OWNED BY altertable_01486_actor;
DROP ROLE IF EXISTS altertable_01486_actor;
DROP TABLE IF EXISTS public.altertable_01486_tbl, altertable_01486_parent CASCADE;
