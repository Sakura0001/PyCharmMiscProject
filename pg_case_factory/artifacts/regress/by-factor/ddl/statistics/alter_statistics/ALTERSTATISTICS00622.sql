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
-- case_id: ALTERSTATISTICS00622
-- source_md: skills/pg-sql-generation/references/statements/ddl/statistics/alter_statistics.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/statistics/alter_statistics.yaml
-- primary_obligation_id: ASTAT-EXT|00622|stxstattarget_query|DROP_STATISTICS_IF_EXISTS
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterstatistics_00622_tab CASCADE;
DROP STATISTICS IF EXISTS alterstatistics_00622_stx CASCADE;
DROP OWNED BY alterstatistics_00622_newowner CASCADE;
DROP ROLE IF EXISTS alterstatistics_00622_newowner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterstatistics_00622_newowner LOGIN;
CREATE TABLE alterstatistics_00622_tab (alterstatistics_00622_c1 integer, alterstatistics_00622_c2 integer);
CREATE STATISTICS alterstatistics_00622_stx ON alterstatistics_00622_tab (alterstatistics_00622_c1, alterstatistics_00622_c2);
-- 3. 执行唯一获得覆盖信用的 ALTER STATISTICS。
-- primary-target-begin
ALTER STATISTICS alterstatistics_00622_stx OWNER TO CURRENT_ROLE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS stats_target_state FROM pg_catalog.pg_statistic_ext WHERE stxname = 'alterstatistics_00622_stx' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP STATISTICS IF EXISTS alterstatistics_00622_stx CASCADE;
DROP OWNED BY alterstatistics_00622_newowner CASCADE;
DROP ROLE IF EXISTS alterstatistics_00622_newowner;
DROP TABLE IF EXISTS alterstatistics_00622_tab CASCADE;
