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
-- case_id: ALTERTABLE04005
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/alter_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/alter_table.yaml
-- primary_obligation_id: ALT-TBL-EXT|04005|add_column|SELECT_inspection|DROP_TABLE_CASCADE
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS public.altertable_04005_tbl, altertable_04005_parent CASCADE;
DROP SCHEMA IF EXISTS altertable_04005_sch CASCADE;
DROP ROLE IF EXISTS altertable_04005_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地表和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS altertable_04005_sch;
CREATE ROLE altertable_04005_owner LOGIN;
GRANT USAGE ON SCHEMA public TO altertable_04005_owner;
CREATE TABLE public.altertable_04005_tbl (altertable_04005_id integer PRIMARY KEY, altertable_04005_col integer, altertable_04005_txt text);
CREATE TABLE altertable_04005_parent (altertable_04005_id integer PRIMARY KEY, altertable_04005_col integer);
ALTER TABLE public.altertable_04005_tbl OWNER TO altertable_04005_owner;
SET ROLE altertable_04005_owner;
-- 3. 执行唯一获得覆盖信用的 ALTER TABLE。
-- primary-target-begin
ALTER TABLE IF EXISTS altertable_04005_sch.altertable_04005_tbl ADD altertable_04005_col integer;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS row_count FROM altertable_04005_tbl ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP SCHEMA IF EXISTS altertable_04005_sch CASCADE;
DROP OWNED BY altertable_04005_owner;
DROP ROLE IF EXISTS altertable_04005_owner;
DROP TABLE IF EXISTS public.altertable_04005_tbl, altertable_04005_parent CASCADE;
