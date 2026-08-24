-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER STATISTICS set_schema_behavior=nonexistent_schema
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERSTATISTICS01051
-- source_md: skills/pg-sql-generation/references/statements/ddl/statistics/alter_statistics.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/statistics/alter_statistics.yaml
-- primary_obligation_id: ASTAT-EXT|01051|error_assertion|DROP_STATISTICS_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 3F000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterstatistics_01051_tab CASCADE;
DROP STATISTICS IF EXISTS alterstatistics_01051_stxsch.alterstatistics_01051_stx CASCADE;
DROP SCHEMA IF EXISTS alterstatistics_01051_stxsch CASCADE;
DROP OWNED BY alterstatistics_01051_tabowner CASCADE;
DROP ROLE IF EXISTS alterstatistics_01051_tabowner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterstatistics_01051_tabowner LOGIN;
CREATE TABLE alterstatistics_01051_tab (alterstatistics_01051_c1 integer, alterstatistics_01051_c2 integer);
ALTER TABLE alterstatistics_01051_tab OWNER TO alterstatistics_01051_tabowner;
CREATE SCHEMA alterstatistics_01051_stxsch;
SET ROLE alterstatistics_01051_tabowner;
CREATE STATISTICS alterstatistics_01051_stxsch.alterstatistics_01051_stx ON alterstatistics_01051_tab (alterstatistics_01051_c1, alterstatistics_01051_c2);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER STATISTICS。
-- primary-target-begin
ALTER STATISTICS alterstatistics_01051_stxsch.alterstatistics_01051_stx SET SCHEMA alterstatistics_01051_nosch;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '3F000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP STATISTICS IF EXISTS alterstatistics_01051_stxsch.alterstatistics_01051_stx CASCADE;
DROP SCHEMA IF EXISTS alterstatistics_01051_stxsch CASCADE;
DROP OWNED BY alterstatistics_01051_tabowner CASCADE;
DROP ROLE IF EXISTS alterstatistics_01051_tabowner;
DROP TABLE IF EXISTS alterstatistics_01051_tab CASCADE;
