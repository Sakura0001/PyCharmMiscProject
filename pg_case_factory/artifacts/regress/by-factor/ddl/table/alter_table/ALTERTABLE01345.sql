-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TABLE role_dependency=owner_role_not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTABLE01345
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|01345|owner_to|SELECT_inspection|DROP_TABLE_CASCADE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altertable_01345_tbl, altertable_01345_parent CASCADE;
DROP ROLE IF EXISTS altertable_01345_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE ROLE altertable_01345_owner LOGIN;
GRANT USAGE ON SCHEMA public TO altertable_01345_owner;
CREATE TABLE altertable_01345_tbl (altertable_01345_id integer PRIMARY KEY, altertable_01345_col integer, altertable_01345_txt text);
CREATE TABLE altertable_01345_parent (altertable_01345_id integer PRIMARY KEY, altertable_01345_col integer);
ALTER TABLE altertable_01345_tbl OWNER TO altertable_01345_owner;
SET ROLE altertable_01345_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE altertable_01345_tbl OWNER TO altertable_01345_no_such_role;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) AS row_count FROM altertable_01345_tbl ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY altertable_01345_owner;
DROP ROLE IF EXISTS altertable_01345_owner;
DROP TABLE IF EXISTS altertable_01345_tbl, altertable_01345_parent CASCADE;
