-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER STATISTICS statistics_state=non_existent
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERSTATISTICS01033
-- source_md: skills/pg-sql-generation/references/statements/ddl/statistics/alter_statistics.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/statistics/alter_statistics.yaml
-- primary_obligation_id: ASTAT-EXT|01033|error_assertion|DROP_STATISTICS_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterstatistics_01033_tab CASCADE;
DROP STATISTICS IF EXISTS alterstatistics_01033_nostx CASCADE;
DROP SCHEMA IF EXISTS alterstatistics_01033_newsch CASCADE;
DROP OWNED BY alterstatistics_01033_tabowner CASCADE;
DROP ROLE IF EXISTS alterstatistics_01033_tabowner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterstatistics_01033_tabowner LOGIN;
CREATE TABLE alterstatistics_01033_tab (alterstatistics_01033_c1 integer, alterstatistics_01033_c2 integer);
ALTER TABLE alterstatistics_01033_tab OWNER TO alterstatistics_01033_tabowner;
CREATE SCHEMA alterstatistics_01033_newsch;
SET ROLE alterstatistics_01033_tabowner;
SELECT 1 AS target_statistics_intentionally_absent;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER STATISTICS。
-- primary-target-begin
ALTER STATISTICS alterstatistics_01033_nostx SET SCHEMA alterstatistics_01033_newsch;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP STATISTICS IF EXISTS alterstatistics_01033_nostx CASCADE;
DROP SCHEMA IF EXISTS alterstatistics_01033_newsch CASCADE;
DROP OWNED BY alterstatistics_01033_tabowner CASCADE;
DROP ROLE IF EXISTS alterstatistics_01033_tabowner;
DROP TABLE IF EXISTS alterstatistics_01033_tab CASCADE;
