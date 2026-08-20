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
-- case_id: ALTERTABLE00625
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|00625|drop_column|SELECT_inspection|DROP_TABLE_CASCADE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altertable_00625_tbl, altertable_00625_parent CASCADE;
DROP ROLE IF EXISTS altertable_00625_owner;
DROP ROLE IF EXISTS altertable_00625_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE ROLE altertable_00625_owner LOGIN;
CREATE ROLE altertable_00625_actor LOGIN;
GRANT USAGE ON SCHEMA public TO altertable_00625_owner;
GRANT USAGE ON SCHEMA public TO altertable_00625_actor;
CREATE TABLE altertable_00625_tbl (altertable_00625_id integer PRIMARY KEY, altertable_00625_col integer, altertable_00625_txt text);
CREATE TABLE altertable_00625_parent (altertable_00625_id integer PRIMARY KEY, altertable_00625_col integer);
ALTER TABLE altertable_00625_tbl OWNER TO altertable_00625_owner;
SET ROLE altertable_00625_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE altertable_00625_tbl DROP altertable_00625_col;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) AS row_count FROM altertable_00625_tbl ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY altertable_00625_owner;
DROP ROLE IF EXISTS altertable_00625_owner;
DROP OWNED BY altertable_00625_actor;
DROP ROLE IF EXISTS altertable_00625_actor;
DROP TABLE IF EXISTS altertable_00625_tbl, altertable_00625_parent CASCADE;
