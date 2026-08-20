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
-- case_id: ALTERTABLE04390
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|04390|alter_column_type|pg_class_catalog_query|ALTER_TABLE_REVERT
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS public.altertable_04390_tbl, altertable_04390_parent CASCADE;
DROP SCHEMA IF EXISTS altertable_04390_sch CASCADE;
DROP ROLE IF EXISTS altertable_04390_owner;
DROP ROLE IF EXISTS altertable_04390_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altertable_04390_sch;
CREATE ROLE altertable_04390_owner LOGIN;
CREATE ROLE altertable_04390_actor LOGIN;
GRANT USAGE ON SCHEMA public TO altertable_04390_owner;
GRANT USAGE ON SCHEMA public TO altertable_04390_actor;
CREATE TABLE public.altertable_04390_tbl (altertable_04390_id integer PRIMARY KEY, altertable_04390_col integer, altertable_04390_txt text);
CREATE TABLE altertable_04390_parent (altertable_04390_id integer PRIMARY KEY, altertable_04390_col integer);
ALTER TABLE public.altertable_04390_tbl OWNER TO altertable_04390_owner;
SET ROLE altertable_04390_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE altertable_04390_sch.altertable_04390_tbl ALTER altertable_04390_col TYPE integer;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) AS table_exists FROM pg_catalog.pg_class WHERE relname = 'altertable_04390_tbl' AND relkind = 'r' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS altertable_04390_sch CASCADE;
DROP OWNED BY altertable_04390_owner;
DROP ROLE IF EXISTS altertable_04390_owner;
DROP OWNED BY altertable_04390_actor;
DROP ROLE IF EXISTS altertable_04390_actor;
DROP TABLE IF EXISTS public.altertable_04390_tbl, altertable_04390_parent CASCADE;
