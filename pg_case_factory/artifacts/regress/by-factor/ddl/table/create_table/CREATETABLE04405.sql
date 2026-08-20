-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TABLE object_state=already_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETABLE04405
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/create_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/create_table.yaml
-- primary_obligation_id: CT-EXT|04405|pg_attribute_query|DROP_TABLE|secondary_table_name_shape
-- expected_outcome: expected_failure
-- expected_sqlstate: 42710
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createtable_04405_t CASCADE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地表和因子专用夹具。
CREATE TABLE createtable_04405_t (createtable_04405_col integer);
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE TABLE。
-- primary-target-begin
CREATE TABLE createtable_04405_t (createtable_04405_col integer NOT NULL);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42710' AS target_sqlstate_matches_expected;
SELECT count(*) AS attr_count FROM pg_catalog.pg_attribute WHERE attrelid = 'createtable_04405_t'::regclass ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS createtable_04405_t CASCADE;
