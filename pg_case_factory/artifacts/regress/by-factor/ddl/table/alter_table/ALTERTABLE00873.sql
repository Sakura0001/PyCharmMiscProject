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
-- case_id: ALTERTABLE00873
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|00873|drop_column|pg_attribute_query|DROP_TABLE_CASCADE
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altertable_00873_tbl, altertable_00873_parent CASCADE;
DROP ROLE IF EXISTS altertable_00873_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE ROLE altertable_00873_owner LOGIN;
GRANT USAGE ON SCHEMA public TO altertable_00873_owner;
CREATE TABLE altertable_00873_tbl (altertable_00873_id integer PRIMARY KEY, altertable_00873_col integer, altertable_00873_txt text);
CREATE TABLE altertable_00873_parent (altertable_00873_id integer PRIMARY KEY, altertable_00873_col integer);
ALTER TABLE altertable_00873_tbl OWNER TO altertable_00873_owner;
SET ROLE altertable_00873_owner;
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE IF EXISTS "altertable_00873_Mixed Table" DROP altertable_00873_col;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT a.attname, a.attnum FROM pg_catalog.pg_attribute AS a WHERE a.attrelid = 'altertable_00873_Mixed Table'::regclass AND a.attnum > 0 ORDER BY a.attname;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY altertable_00873_owner;
DROP ROLE IF EXISTS altertable_00873_owner;
DROP TABLE IF EXISTS altertable_00873_tbl, altertable_00873_parent CASCADE;
