-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE STATISTICS statement_branch=branch_multivariate_columns
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATESTATISTICS01089
-- source_md: skills/pg-sql-generation/references/statements/ddl/statistics/create_statistics.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/statistics/create_statistics.yaml
-- primary_obligation_id: CSTAT-EXT|01089|pg_statistic_ext_catalog|drop_statistics|secondary_statistics_name_shape
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createstatistics_01089_t CASCADE;
DROP STATISTICS IF EXISTS createstatistics_01089_stat;
DROP STATISTICS IF EXISTS createstatistics_01089_statnew;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地表和因子专用夹具。
CREATE TABLE createstatistics_01089_t (a integer, b integer, c integer, d text);
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE STATISTICS。
-- primary-target-begin
CREATE STATISTICS public.createstatistics_01089_stat (ndistinct, dependencies, mcv) ON (a, b, c) FROM createstatistics_01089_t;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS stat_count FROM pg_catalog.pg_statistic_ext s JOIN pg_catalog.pg_class c ON c.oid = s.stxrelid WHERE c.relname = 'createstatistics_01089_t' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP STATISTICS IF EXISTS createstatistics_01089_stat;
DROP STATISTICS IF EXISTS createstatistics_01089_statnew;
DROP TABLE IF EXISTS createstatistics_01089_t CASCADE;
