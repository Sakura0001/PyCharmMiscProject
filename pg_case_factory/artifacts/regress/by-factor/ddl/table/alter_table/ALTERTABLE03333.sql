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
-- case_id: ALTERTABLE03333
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|03333|set_schema|pg_attribute_query|DROP_TABLE_CASCADE
-- expected_outcome: expected_failure
-- expected_sqlstate: 3F000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altertable_03333_tbl, altertable_03333_parent CASCADE;
DROP SCHEMA IF EXISTS altertable_03333_new_sch CASCADE;
DROP ROLE IF EXISTS altertable_03333_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altertable_03333_new_sch;
CREATE ROLE altertable_03333_owner LOGIN;
GRANT USAGE ON SCHEMA public TO altertable_03333_owner;
CREATE TABLE altertable_03333_tbl (altertable_03333_id integer PRIMARY KEY, altertable_03333_col integer, altertable_03333_txt text);
CREATE TABLE altertable_03333_parent (altertable_03333_id integer PRIMARY KEY, altertable_03333_col integer);
ALTER TABLE altertable_03333_tbl OWNER TO altertable_03333_owner;
SET ROLE altertable_03333_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE IF EXISTS altertable_03333_tbl SET SCHEMA altertable_03333_no_such_sch;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '3F000' AS target_sqlstate_matches_expected;
SELECT a.attname, a.attnum FROM pg_catalog.pg_attribute AS a WHERE a.attrelid = 'altertable_03333_tbl'::regclass AND a.attnum > 0 ORDER BY a.attname;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS altertable_03333_new_sch CASCADE;
DROP OWNED BY altertable_03333_owner;
DROP ROLE IF EXISTS altertable_03333_owner;
DROP TABLE IF EXISTS altertable_03333_tbl, altertable_03333_parent CASCADE;
