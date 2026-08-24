-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE STATISTICS column_dependency=column_not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATESTATISTICS00009
-- source_md: skills/pg-sql-generation/references/statements/ddl/statistics/create_statistics.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/statistics/create_statistics.yaml
-- primary_obligation_id: CSTAT-SFV|sfv-474cd7a4bccc1bf84597b9b0|nonexistent_column
-- expected_outcome: expected_failure
-- expected_sqlstate: 42703
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createstatistics_00009_t CASCADE;
DROP STATISTICS IF EXISTS createstatistics_00009_stat;
DROP STATISTICS IF EXISTS createstatistics_00009_statnew;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地表和因子专用夹具。
CREATE TABLE createstatistics_00009_t (a integer, b integer, c integer, d text);
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE STATISTICS。
-- primary-target-begin
CREATE STATISTICS createstatistics_00009_stat ON (a, zzz) FROM createstatistics_00009_t;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42703' AS target_sqlstate_matches_expected;
SELECT count(*) AS stat_count FROM pg_catalog.pg_statistic_ext s JOIN pg_catalog.pg_class c ON c.oid = s.stxrelid WHERE c.relname = 'createstatistics_00009_t' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP STATISTICS IF EXISTS createstatistics_00009_stat;
DROP STATISTICS IF EXISTS createstatistics_00009_statnew;
DROP TABLE IF EXISTS createstatistics_00009_t CASCADE;
