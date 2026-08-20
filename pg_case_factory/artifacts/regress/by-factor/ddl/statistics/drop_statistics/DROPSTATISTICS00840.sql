-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : DROP STATISTICS statistics_existence=statistics_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPSTATISTICS00840
-- source_md: skills/pg-sql-generation/references/statements/ddl/statistics/drop_statistics.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/statistics/drop_statistics.yaml
-- primary_obligation_id: DROPSTATISTICS-EXT|00840|drop_statistics|pg_statistic_ext_catalog|drop_statistics
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropstatistics_00840_t CASCADE;
DROP STATISTICS IF EXISTS public.dropstatistics_00840_stat;
\set ON_ERROR_STOP on
-- 2. 创建完整本地统计和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE TABLE dropstatistics_00840_t (c1 integer, c2 integer);
SELECT 1 AS target_statistics_intentionally_absent;
-- 3. 执行唯一获得覆盖信用的 DROP STATISTICS。
-- primary-target-begin
DROP STATISTICS IF EXISTS public.dropstatistics_00840_stat CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS statistics_absent FROM pg_catalog.pg_statistic_ext WHERE stxname = 'dropstatistics_00840_stat' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP STATISTICS IF EXISTS public.dropstatistics_00840_stat;
DROP TABLE IF EXISTS dropstatistics_00840_t CASCADE;
