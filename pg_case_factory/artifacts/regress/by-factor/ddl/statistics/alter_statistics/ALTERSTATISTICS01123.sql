-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER STATISTICS statistics_target_value=out_of_range
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERSTATISTICS01123
-- source_md: skills/pg-sql-generation/references/statements/ddl/statistics/alter_statistics.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/statistics/alter_statistics.yaml
-- primary_obligation_id: ASTAT-EXT|01123|error_assertion|DROP_STATISTICS_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 22023
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterstatistics_01123_tab CASCADE;
DROP STATISTICS IF EXISTS alterstatistics_01123_stxsch.alterstatistics_01123_stx CASCADE;
DROP SCHEMA IF EXISTS alterstatistics_01123_stxsch CASCADE;
DROP OWNED BY alterstatistics_01123_tabowner CASCADE;
DROP ROLE IF EXISTS alterstatistics_01123_tabowner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterstatistics_01123_tabowner LOGIN;
CREATE TABLE alterstatistics_01123_tab (alterstatistics_01123_c1 integer, alterstatistics_01123_c2 integer);
ALTER TABLE alterstatistics_01123_tab OWNER TO alterstatistics_01123_tabowner;
CREATE SCHEMA alterstatistics_01123_stxsch;
SET ROLE alterstatistics_01123_tabowner;
CREATE STATISTICS alterstatistics_01123_stxsch.alterstatistics_01123_stx ON alterstatistics_01123_tab (alterstatistics_01123_c1, alterstatistics_01123_c2);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER STATISTICS。
-- primary-target-begin
ALTER STATISTICS alterstatistics_01123_stxsch.alterstatistics_01123_stx SET STATISTICS 99999;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '22023' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP STATISTICS IF EXISTS alterstatistics_01123_stxsch.alterstatistics_01123_stx CASCADE;
DROP SCHEMA IF EXISTS alterstatistics_01123_stxsch CASCADE;
DROP OWNED BY alterstatistics_01123_tabowner CASCADE;
DROP ROLE IF EXISTS alterstatistics_01123_tabowner;
DROP TABLE IF EXISTS alterstatistics_01123_tab CASCADE;
