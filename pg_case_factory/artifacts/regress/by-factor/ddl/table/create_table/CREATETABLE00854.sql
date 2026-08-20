-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TABLE table_type=permanent
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETABLE00854
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/create_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/create_table.yaml
-- primary_obligation_id: CT-EXT|00854|information_schema_tables|DROP_TABLE_IF_EXISTS|main
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createtable_00854_t CASCADE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地表和因子专用夹具。
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE TABLE。
-- primary-target-begin
CREATE TABLE createtable_00854_t (createtable_00854_col integer) PARTITION BY LIST (createtable_00854_col);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS table_count FROM information_schema.tables WHERE table_name = 'createtable_00854_t' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS createtable_00854_t;
