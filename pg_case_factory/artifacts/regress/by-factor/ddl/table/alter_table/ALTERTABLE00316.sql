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
-- case_id: ALTERTABLE00316
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|00316|drop_column|pg_constraint_query|DROP_TABLE_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altertable_00316_tbl, altertable_00316_parent CASCADE;
DROP ROLE IF EXISTS altertable_00316_owner;
DROP ROLE IF EXISTS altertable_00316_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE ROLE altertable_00316_owner LOGIN;
CREATE ROLE altertable_00316_actor LOGIN;
GRANT USAGE ON SCHEMA public TO altertable_00316_owner;
GRANT USAGE ON SCHEMA public TO altertable_00316_actor;
CREATE TABLE altertable_00316_tbl (altertable_00316_id integer PRIMARY KEY, altertable_00316_col integer, altertable_00316_txt text);
CREATE TABLE altertable_00316_parent (altertable_00316_id integer PRIMARY KEY, altertable_00316_col integer);
ALTER TABLE altertable_00316_tbl OWNER TO altertable_00316_owner;
SET ROLE altertable_00316_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE IF EXISTS altertable_00316_tbl DROP altertable_00316_col;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT c.conname, c.contype FROM pg_catalog.pg_constraint AS c WHERE c.conrelid = 'altertable_00316_tbl'::regclass ORDER BY c.conname;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY altertable_00316_owner;
DROP ROLE IF EXISTS altertable_00316_owner;
DROP OWNED BY altertable_00316_actor;
DROP ROLE IF EXISTS altertable_00316_actor;
DROP TABLE IF EXISTS altertable_00316_tbl, altertable_00316_parent CASCADE;
