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
-- case_id: ALTERTABLE04491
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|04491|alter_column_type|pg_class_catalog_query|RESET_STATE
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altertable_04491_tbl, altertable_04491_parent CASCADE;
DROP ROLE IF EXISTS altertable_04491_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE ROLE altertable_04491_owner LOGIN;
GRANT USAGE ON SCHEMA public TO altertable_04491_owner;
CREATE TABLE altertable_04491_tbl (altertable_04491_id integer PRIMARY KEY, altertable_04491_col integer, altertable_04491_txt text);
CREATE TABLE altertable_04491_parent (altertable_04491_id integer PRIMARY KEY, altertable_04491_col integer);
ALTER TABLE altertable_04491_tbl OWNER TO altertable_04491_owner;
SET ROLE altertable_04491_owner;
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE "altertable_04491_Mixed Table" ALTER altertable_04491_col TYPE integer;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS table_exists FROM pg_catalog.pg_class WHERE relname = 'altertable_04491_Mixed Table' AND relkind = 'r' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY altertable_04491_owner;
DROP ROLE IF EXISTS altertable_04491_owner;
DROP TABLE IF EXISTS altertable_04491_tbl, altertable_04491_parent CASCADE;
