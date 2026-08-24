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
-- case_id: ALTERTABLE01369
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|01369|add_column|pg_class_catalog_query|DROP_TABLE_CASCADE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS public.altertable_01369_tbl, altertable_01369_parent CASCADE;
DROP SCHEMA IF EXISTS altertable_01369_sch CASCADE;
DROP ROLE IF EXISTS altertable_01369_owner;
DROP ROLE IF EXISTS altertable_01369_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altertable_01369_sch;
CREATE ROLE altertable_01369_owner LOGIN;
CREATE ROLE altertable_01369_actor LOGIN;
GRANT USAGE ON SCHEMA public TO altertable_01369_owner;
GRANT USAGE ON SCHEMA public TO altertable_01369_actor;
CREATE TABLE public.altertable_01369_tbl (altertable_01369_id integer PRIMARY KEY, altertable_01369_col integer, altertable_01369_txt text);
CREATE TABLE altertable_01369_parent (altertable_01369_id integer PRIMARY KEY, altertable_01369_col integer);
ALTER TABLE public.altertable_01369_tbl OWNER TO altertable_01369_owner;
SET ROLE altertable_01369_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE altertable_01369_sch.altertable_01369_tbl ADD altertable_01369_col integer;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) AS table_exists FROM pg_catalog.pg_class WHERE relname = 'altertable_01369_tbl' AND relkind = 'r' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS altertable_01369_sch CASCADE;
DROP OWNED BY altertable_01369_owner;
DROP ROLE IF EXISTS altertable_01369_owner;
DROP OWNED BY altertable_01369_actor;
DROP ROLE IF EXISTS altertable_01369_actor;
DROP TABLE IF EXISTS public.altertable_01369_tbl, altertable_01369_parent CASCADE;
