-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER STATISTICS target_action=set_statistics
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERSTATISTICS00842
-- source_md: skills/pg-sql-generation/references/statements/ddl/statistics/alter_statistics.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/statistics/alter_statistics.yaml
-- primary_obligation_id: ASTAT-EXT|00842|pg_statistic_ext_catalog|DROP_STATISTICS_CASCADE
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterstatistics_00842_tab CASCADE;
DROP STATISTICS IF EXISTS alterstatistics_00842_stxsch.alterstatistics_00842_stx CASCADE;
DROP SCHEMA IF EXISTS alterstatistics_00842_stxsch CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE alterstatistics_00842_tab (alterstatistics_00842_c1 integer, alterstatistics_00842_c2 integer);
CREATE SCHEMA alterstatistics_00842_stxsch;
CREATE STATISTICS alterstatistics_00842_stxsch.alterstatistics_00842_stx ON alterstatistics_00842_tab (alterstatistics_00842_c1, alterstatistics_00842_c2);
-- 3. 执行唯一获得覆盖信用的 ALTER STATISTICS。
-- primary-target-begin
ALTER STATISTICS alterstatistics_00842_stxsch.alterstatistics_00842_stx SET STATISTICS 10000;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS stats_state FROM pg_catalog.pg_statistic_ext WHERE stxname = 'alterstatistics_00842_stx' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP STATISTICS IF EXISTS alterstatistics_00842_stxsch.alterstatistics_00842_stx CASCADE;
DROP SCHEMA IF EXISTS alterstatistics_00842_stxsch CASCADE;
DROP TABLE IF EXISTS alterstatistics_00842_tab CASCADE;
