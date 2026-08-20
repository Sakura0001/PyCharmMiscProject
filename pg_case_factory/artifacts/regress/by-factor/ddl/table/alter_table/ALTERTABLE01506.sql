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
-- case_id: ALTERTABLE01506
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|01506|add_column|SELECT_inspection|ALTER_TABLE_REVERT
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altertable_01506_tbl, altertable_01506_parent CASCADE;
DROP ROLE IF EXISTS altertable_01506_owner;
DROP ROLE IF EXISTS altertable_01506_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE ROLE altertable_01506_owner LOGIN;
CREATE ROLE altertable_01506_actor LOGIN;
GRANT USAGE ON SCHEMA public TO altertable_01506_owner;
GRANT USAGE ON SCHEMA public TO altertable_01506_actor;
CREATE TABLE altertable_01506_tbl (altertable_01506_id integer PRIMARY KEY, altertable_01506_col integer, altertable_01506_txt text);
CREATE TABLE altertable_01506_parent (altertable_01506_id integer PRIMARY KEY, altertable_01506_col integer);
ALTER TABLE altertable_01506_tbl OWNER TO altertable_01506_owner;
SET ROLE altertable_01506_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE IF EXISTS altertable_01506_tbl ADD altertable_01506_col integer;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) AS row_count FROM altertable_01506_tbl ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY altertable_01506_owner;
DROP ROLE IF EXISTS altertable_01506_owner;
DROP OWNED BY altertable_01506_actor;
DROP ROLE IF EXISTS altertable_01506_actor;
DROP TABLE IF EXISTS altertable_01506_tbl, altertable_01506_parent CASCADE;
