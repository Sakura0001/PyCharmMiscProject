-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER STATISTICS executor_privilege=non_owner_no_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERSTATISTICS00174
-- source_md: skills/pg-sql-generation/references/statements/ddl/statistics/alter_statistics.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/statistics/alter_statistics.yaml
-- primary_obligation_id: ASTAT-EXT|00174|pg_statistic_ext_catalog|DROP_STATISTICS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterstatistics_00174_tab CASCADE;
DROP STATISTICS IF EXISTS alterstatistics_00174_stxsch.alterstatistics_00174_stx CASCADE;
DROP STATISTICS IF EXISTS "alterstatistics_00174_New Mix" CASCADE;
DROP SCHEMA IF EXISTS alterstatistics_00174_stxsch CASCADE;
DROP OWNED BY alterstatistics_00174_actor CASCADE;
DROP ROLE IF EXISTS alterstatistics_00174_actor;
DROP OWNED BY alterstatistics_00174_tabowner CASCADE;
DROP ROLE IF EXISTS alterstatistics_00174_tabowner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterstatistics_00174_tabowner LOGIN;
CREATE ROLE alterstatistics_00174_actor LOGIN NOSUPERUSER;
CREATE TABLE alterstatistics_00174_tab (alterstatistics_00174_c1 integer, alterstatistics_00174_c2 integer);
ALTER TABLE alterstatistics_00174_tab OWNER TO alterstatistics_00174_tabowner;
CREATE SCHEMA alterstatistics_00174_stxsch;
SET ROLE alterstatistics_00174_tabowner;
CREATE STATISTICS alterstatistics_00174_stxsch.alterstatistics_00174_stx ON alterstatistics_00174_tab (alterstatistics_00174_c1, alterstatistics_00174_c2);
RESET ROLE;
SET ROLE alterstatistics_00174_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER STATISTICS。
-- primary-target-begin
ALTER STATISTICS alterstatistics_00174_stxsch.alterstatistics_00174_stx RENAME TO "alterstatistics_00174_New Mix";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS stats_state FROM pg_catalog.pg_statistic_ext WHERE stxname = 'alterstatistics_00174_stx' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP STATISTICS IF EXISTS alterstatistics_00174_stxsch.alterstatistics_00174_stx CASCADE;
DROP STATISTICS IF EXISTS "alterstatistics_00174_New Mix" CASCADE;
DROP SCHEMA IF EXISTS alterstatistics_00174_stxsch CASCADE;
DROP OWNED BY alterstatistics_00174_actor CASCADE;
DROP ROLE IF EXISTS alterstatistics_00174_actor;
DROP OWNED BY alterstatistics_00174_tabowner CASCADE;
DROP ROLE IF EXISTS alterstatistics_00174_tabowner;
DROP TABLE IF EXISTS alterstatistics_00174_tab CASCADE;
