-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TABLE AS table_type=temp_short
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETABLEAS02673
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/create_table_as.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/create_table_as.yaml
-- primary_obligation_id: CTAS-EXT|02673|information_schema_columns|DROP_TABLE|secondary_table_name_shape
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createtableas_02673_fx CASCADE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地表和因子专用夹具。
CREATE TABLE createtableas_02673_fx (id integer);
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE TABLE AS。
-- primary-target-begin
CREATE TEMP TABLE "createtableas_02673_abort" AS SELECT 1 AS col1, 2 AS col2;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS col_count FROM information_schema.columns WHERE table_name = 'createtableas_02673_abort' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLE createtableas_02673_abort CASCADE;
DROP TABLE IF EXISTS createtableas_02673_fx CASCADE;
