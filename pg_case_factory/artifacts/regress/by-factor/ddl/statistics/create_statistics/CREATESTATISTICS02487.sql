-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE STATISTICS duplicate_statistics_name=same_name_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATESTATISTICS02487
-- source_md: skills/pg-sql-generation/references/statements/ddl/statistics/create_statistics.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/statistics/create_statistics.yaml
-- primary_obligation_id: CSTAT-EXT|02487|error_assertion|drop_statistics|secondary_statistics_identity
-- expected_outcome: expected_failure
-- expected_sqlstate: 42710
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createstatistics_02487_t CASCADE;
DROP STATISTICS IF EXISTS createstatistics_02487_stat;
DROP STATISTICS IF EXISTS createstatistics_02487_statnew;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地表和因子专用夹具。
CREATE TABLE createstatistics_02487_t (a integer, b integer, c integer, d text);
CREATE STATISTICS createstatistics_02487_stat ON (a, b) FROM createstatistics_02487_t;
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE STATISTICS。
-- primary-target-begin
CREATE STATISTICS createstatistics_02487_stat ON (a) FROM createstatistics_02487_t;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42710' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP STATISTICS IF EXISTS createstatistics_02487_stat;
DROP STATISTICS IF EXISTS createstatistics_02487_statnew;
DROP TABLE IF EXISTS createstatistics_02487_t CASCADE;
