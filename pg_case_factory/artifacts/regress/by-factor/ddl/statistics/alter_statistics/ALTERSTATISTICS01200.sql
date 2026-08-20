-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER STATISTICS target_action=owner_to
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERSTATISTICS01200
-- source_md: skills/pg-sql-generation/references/statements/ddl/statistics/alter_statistics.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/statistics/alter_statistics.yaml
-- primary_obligation_id: ASTAT-EXT|01200|pg_statistic_ext_catalog|DROP_STATISTICS
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterstatistics_01200_tab CASCADE;
DROP STATISTICS IF EXISTS alterstatistics_01200_stxsch.alterstatistics_01200_stx CASCADE;
DROP SCHEMA IF EXISTS alterstatistics_01200_stxsch CASCADE;
DROP OWNED BY alterstatistics_01200_newowner CASCADE;
DROP ROLE IF EXISTS alterstatistics_01200_newowner;
DROP OWNED BY alterstatistics_01200_tabowner CASCADE;
DROP ROLE IF EXISTS alterstatistics_01200_tabowner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterstatistics_01200_tabowner LOGIN;
CREATE ROLE alterstatistics_01200_newowner LOGIN;
CREATE TABLE alterstatistics_01200_tab (alterstatistics_01200_c1 integer, alterstatistics_01200_c2 integer);
ALTER TABLE alterstatistics_01200_tab OWNER TO alterstatistics_01200_tabowner;
CREATE SCHEMA alterstatistics_01200_stxsch;
SET ROLE alterstatistics_01200_tabowner;
CREATE STATISTICS alterstatistics_01200_stxsch.alterstatistics_01200_stx ON alterstatistics_01200_tab (alterstatistics_01200_c1, alterstatistics_01200_c2);
-- 3. 执行唯一获得覆盖信用的 ALTER STATISTICS。
-- primary-target-begin
ALTER STATISTICS alterstatistics_01200_stxsch.alterstatistics_01200_stx OWNER TO alterstatistics_01200_newowner;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS stats_state FROM pg_catalog.pg_statistic_ext WHERE stxname = 'alterstatistics_01200_stx' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP STATISTICS IF EXISTS alterstatistics_01200_stxsch.alterstatistics_01200_stx CASCADE;
DROP SCHEMA IF EXISTS alterstatistics_01200_stxsch CASCADE;
DROP OWNED BY alterstatistics_01200_newowner CASCADE;
DROP ROLE IF EXISTS alterstatistics_01200_newowner;
DROP OWNED BY alterstatistics_01200_tabowner CASCADE;
DROP ROLE IF EXISTS alterstatistics_01200_tabowner;
DROP TABLE IF EXISTS alterstatistics_01200_tab CASCADE;
