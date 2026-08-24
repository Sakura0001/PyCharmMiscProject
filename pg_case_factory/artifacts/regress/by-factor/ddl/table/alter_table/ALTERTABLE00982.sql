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
-- case_id: ALTERTABLE00982
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|00982|add_column|information_schema_query|ALTER_TABLE_REVERT
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altertable_00982_tbl, altertable_00982_parent CASCADE;
DROP ROLE IF EXISTS altertable_00982_owner;
DROP ROLE IF EXISTS altertable_00982_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE ROLE altertable_00982_owner LOGIN;
CREATE ROLE altertable_00982_actor LOGIN;
GRANT USAGE ON SCHEMA public TO altertable_00982_owner;
GRANT USAGE ON SCHEMA public TO altertable_00982_actor;
CREATE TABLE altertable_00982_tbl (altertable_00982_id integer PRIMARY KEY, altertable_00982_col integer, altertable_00982_txt text);
CREATE TABLE altertable_00982_parent (altertable_00982_id integer PRIMARY KEY, altertable_00982_col integer);
ALTER TABLE altertable_00982_tbl OWNER TO altertable_00982_owner;
SET ROLE altertable_00982_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE "altertable_00982_Mixed Table" ADD altertable_00982_col integer;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT column_name, data_type FROM information_schema.columns WHERE table_name = 'altertable_00982_Mixed Table' ORDER BY column_name;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY altertable_00982_owner;
DROP ROLE IF EXISTS altertable_00982_owner;
DROP OWNED BY altertable_00982_actor;
DROP ROLE IF EXISTS altertable_00982_actor;
DROP TABLE IF EXISTS altertable_00982_tbl, altertable_00982_parent CASCADE;
