-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TABLE object_state=exists_normal
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTABLE00926
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|00926|drop_column|SELECT_inspection|ALTER_TABLE_REVERT
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altertable_00926_tbl, altertable_00926_parent CASCADE;
DROP ROLE IF EXISTS altertable_00926_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE ROLE altertable_00926_owner LOGIN;
GRANT USAGE ON SCHEMA public TO altertable_00926_owner;
CREATE TABLE altertable_00926_tbl (altertable_00926_id integer PRIMARY KEY, altertable_00926_col integer, altertable_00926_txt text);
CREATE TABLE altertable_00926_parent (altertable_00926_id integer PRIMARY KEY, altertable_00926_col integer);
ALTER TABLE altertable_00926_tbl OWNER TO altertable_00926_owner;
SET ROLE altertable_00926_owner;
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE IF EXISTS altertable_00926_tbl DROP altertable_00926_col;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS row_count FROM altertable_00926_tbl ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY altertable_00926_owner;
DROP ROLE IF EXISTS altertable_00926_owner;
DROP TABLE IF EXISTS altertable_00926_tbl, altertable_00926_parent CASCADE;
