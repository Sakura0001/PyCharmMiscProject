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
-- case_id: ALTERSTATISTICS00280
-- source_md: skills/pg-sql-generation/references/statements/ddl/statistics/alter_statistics.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/statistics/alter_statistics.yaml
-- primary_obligation_id: ASTAT-EXT|00280|stxstattarget_query|DROP_STATISTICS_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterstatistics_00280_tab CASCADE;
DROP STATISTICS IF EXISTS "alterstatistics_00280_Mix Stx" CASCADE;
DROP OWNED BY alterstatistics_00280_actor CASCADE;
DROP ROLE IF EXISTS alterstatistics_00280_actor;
DROP OWNED BY alterstatistics_00280_tabowner CASCADE;
DROP ROLE IF EXISTS alterstatistics_00280_tabowner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterstatistics_00280_tabowner LOGIN;
CREATE ROLE alterstatistics_00280_actor LOGIN NOSUPERUSER;
CREATE TABLE alterstatistics_00280_tab (alterstatistics_00280_c1 integer, alterstatistics_00280_c2 integer);
ALTER TABLE alterstatistics_00280_tab OWNER TO alterstatistics_00280_tabowner;
SET ROLE alterstatistics_00280_tabowner;
CREATE STATISTICS "alterstatistics_00280_Mix Stx" ON alterstatistics_00280_tab (alterstatistics_00280_c1, alterstatistics_00280_c2);
RESET ROLE;
SET ROLE alterstatistics_00280_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER STATISTICS。
-- primary-target-begin
ALTER STATISTICS "alterstatistics_00280_Mix Stx" SET STATISTICS 1;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS stats_target_state FROM pg_catalog.pg_statistic_ext WHERE stxname = 'alterstatistics_00280_Mix Stx' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP STATISTICS IF EXISTS "alterstatistics_00280_Mix Stx" CASCADE;
DROP OWNED BY alterstatistics_00280_actor CASCADE;
DROP ROLE IF EXISTS alterstatistics_00280_actor;
DROP OWNED BY alterstatistics_00280_tabowner CASCADE;
DROP ROLE IF EXISTS alterstatistics_00280_tabowner;
DROP TABLE IF EXISTS alterstatistics_00280_tab CASCADE;
