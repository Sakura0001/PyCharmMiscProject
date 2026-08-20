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
-- case_id: ALTERTABLE03305
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|03305|set_schema|SELECT_inspection|DROP_TABLE_CASCADE
-- expected_outcome: expected_failure
-- expected_sqlstate: 3F000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altertable_03305_tbl, altertable_03305_parent CASCADE;
DROP ROLE IF EXISTS altertable_03305_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE ROLE altertable_03305_owner LOGIN;
GRANT USAGE ON SCHEMA public TO altertable_03305_owner;
CREATE TABLE altertable_03305_tbl (altertable_03305_id integer PRIMARY KEY, altertable_03305_col integer, altertable_03305_txt text);
CREATE TABLE altertable_03305_parent (altertable_03305_id integer PRIMARY KEY, altertable_03305_col integer);
ALTER TABLE altertable_03305_tbl OWNER TO altertable_03305_owner;
SET ROLE altertable_03305_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE IF EXISTS altertable_03305_tbl SET SCHEMA altertable_03305_new_sch;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '3F000' AS target_sqlstate_matches_expected;
SELECT count(*) AS row_count FROM altertable_03305_tbl ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY altertable_03305_owner;
DROP ROLE IF EXISTS altertable_03305_owner;
DROP TABLE IF EXISTS altertable_03305_tbl, altertable_03305_parent CASCADE;
