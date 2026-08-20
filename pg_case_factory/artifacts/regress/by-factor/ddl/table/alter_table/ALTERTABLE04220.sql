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
-- case_id: ALTERTABLE04220
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|04220|alter_column_type|information_schema_query|DROP_TABLE_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS public.altertable_04220_tbl, altertable_04220_parent CASCADE;
DROP SCHEMA IF EXISTS altertable_04220_sch CASCADE;
DROP ROLE IF EXISTS altertable_04220_owner;
DROP ROLE IF EXISTS altertable_04220_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altertable_04220_sch;
CREATE ROLE altertable_04220_owner LOGIN;
CREATE ROLE altertable_04220_actor LOGIN;
GRANT USAGE ON SCHEMA public TO altertable_04220_owner;
GRANT USAGE ON SCHEMA public TO altertable_04220_actor;
CREATE TABLE public.altertable_04220_tbl (altertable_04220_id integer PRIMARY KEY, altertable_04220_col integer, altertable_04220_txt text);
CREATE TABLE altertable_04220_parent (altertable_04220_id integer PRIMARY KEY, altertable_04220_col integer);
ALTER TABLE public.altertable_04220_tbl OWNER TO altertable_04220_owner;
SET ROLE altertable_04220_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE altertable_04220_sch.altertable_04220_tbl ALTER altertable_04220_col TYPE integer;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'altertable_04220_tbl' ORDER BY column_name;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS altertable_04220_sch CASCADE;
DROP OWNED BY altertable_04220_owner;
DROP ROLE IF EXISTS altertable_04220_owner;
DROP OWNED BY altertable_04220_actor;
DROP ROLE IF EXISTS altertable_04220_actor;
DROP TABLE IF EXISTS public.altertable_04220_tbl, altertable_04220_parent CASCADE;
