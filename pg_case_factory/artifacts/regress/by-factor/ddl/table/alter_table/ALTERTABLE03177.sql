-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TABLE schema_dependency=schema_not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTABLE03177
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|03177|set_schema|pg_constraint_query|DROP_TABLE_CASCADE
-- expected_outcome: expected_failure
-- expected_sqlstate: 3F000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altertable_03177_tbl, altertable_03177_parent CASCADE;
DROP SCHEMA IF EXISTS altertable_03177_new_sch CASCADE;
DROP ROLE IF EXISTS altertable_03177_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altertable_03177_new_sch;
CREATE ROLE altertable_03177_owner LOGIN;
GRANT USAGE ON SCHEMA public TO altertable_03177_owner;
CREATE TABLE altertable_03177_tbl (altertable_03177_id integer PRIMARY KEY, altertable_03177_col integer, altertable_03177_txt text);
CREATE TABLE altertable_03177_parent (altertable_03177_id integer PRIMARY KEY, altertable_03177_col integer);
ALTER TABLE altertable_03177_tbl OWNER TO altertable_03177_owner;
SET ROLE altertable_03177_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE altertable_03177_tbl SET SCHEMA altertable_03177_no_such_sch;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '3F000' AS target_sqlstate_matches_expected;
SELECT c.conname, c.contype FROM pg_catalog.pg_constraint AS c WHERE c.conrelid = 'altertable_03177_tbl'::regclass ORDER BY c.conname;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS altertable_03177_new_sch CASCADE;
DROP OWNED BY altertable_03177_owner;
DROP ROLE IF EXISTS altertable_03177_owner;
DROP TABLE IF EXISTS altertable_03177_tbl, altertable_03177_parent CASCADE;
