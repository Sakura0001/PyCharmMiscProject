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
-- case_id: ALTERTABLE00248
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|00248|drop_column|pg_class_catalog_query|DROP_TABLE_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altertable_00248_tbl, altertable_00248_parent CASCADE;
DROP ROLE IF EXISTS altertable_00248_owner;
DROP ROLE IF EXISTS altertable_00248_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE ROLE altertable_00248_owner LOGIN;
CREATE ROLE altertable_00248_actor LOGIN;
GRANT USAGE ON SCHEMA public TO altertable_00248_owner;
GRANT USAGE ON SCHEMA public TO altertable_00248_actor;
CREATE TABLE altertable_00248_tbl (altertable_00248_id integer PRIMARY KEY, altertable_00248_col integer, altertable_00248_txt text);
CREATE TABLE altertable_00248_parent (altertable_00248_id integer PRIMARY KEY, altertable_00248_col integer);
ALTER TABLE altertable_00248_tbl OWNER TO altertable_00248_owner;
SET ROLE altertable_00248_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE altertable_00248_tbl DROP altertable_00248_col;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) AS table_exists FROM pg_catalog.pg_class WHERE relname = 'altertable_00248_tbl' AND relkind = 'r' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY altertable_00248_owner;
DROP ROLE IF EXISTS altertable_00248_owner;
DROP OWNED BY altertable_00248_actor;
DROP ROLE IF EXISTS altertable_00248_actor;
DROP TABLE IF EXISTS altertable_00248_tbl, altertable_00248_parent CASCADE;
