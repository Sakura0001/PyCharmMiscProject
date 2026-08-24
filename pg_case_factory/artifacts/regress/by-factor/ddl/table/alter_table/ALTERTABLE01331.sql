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
-- case_id: ALTERTABLE01331
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|01331|owner_to|pg_class_catalog_query|RESET_STATE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altertable_01331_tbl, altertable_01331_parent CASCADE;
DROP ROLE IF EXISTS altertable_01331_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE ROLE altertable_01331_owner LOGIN;
GRANT USAGE ON SCHEMA public TO altertable_01331_owner;
CREATE TABLE altertable_01331_tbl (altertable_01331_id integer PRIMARY KEY, altertable_01331_col integer, altertable_01331_txt text);
CREATE TABLE altertable_01331_parent (altertable_01331_id integer PRIMARY KEY, altertable_01331_col integer);
ALTER TABLE altertable_01331_tbl OWNER TO altertable_01331_owner;
SET ROLE altertable_01331_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE altertable_01331_tbl OWNER TO altertable_01331_no_such_role;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) AS table_exists FROM pg_catalog.pg_class WHERE relname = 'altertable_01331_tbl' AND relkind = 'r' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY altertable_01331_owner;
DROP ROLE IF EXISTS altertable_01331_owner;
DROP TABLE IF EXISTS altertable_01331_tbl, altertable_01331_parent CASCADE;
