-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TABLE AS query_error=aggregate_mismatch
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETABLEAS00038
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/create_table_as.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/create_table_as.yaml
-- primary_obligation_id: CTAS-SFV|sfv-c060e1084cd2584fa0b03f92|regular
-- expected_outcome: expected_failure
-- expected_sqlstate: 42803
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createtableas_00038_src, createtableas_00038_t CASCADE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地表和因子专用夹具。
CREATE TABLE createtableas_00038_src (id integer, val text, id2 integer);
INSERT INTO createtableas_00038_src VALUES (1, 'a', 10), (2, 'b', 20);
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE TABLE AS。
-- primary-target-begin
CREATE TABLE createtableas_00038_t (col1, col2, extra) AS SELECT count(*) AS cnt, max(id) AS mx FROM createtableas_00038_src;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42803' AS target_sqlstate_matches_expected;
SELECT count(*) AS target_created_count FROM pg_catalog.pg_class c WHERE c.relname = 'createtableas_00038_t' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS createtableas_00038_src, createtableas_00038_t CASCADE;
