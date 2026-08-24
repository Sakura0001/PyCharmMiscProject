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
-- case_id: ALTERSTATISTICS00674
-- source_md: skills/pg-sql-generation/references/statements/ddl/statistics/alter_statistics.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/statistics/alter_statistics.yaml
-- primary_obligation_id: ASTAT-EXT|00674|error_assertion|DROP_STATISTICS_CASCADE
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterstatistics_00674_tab CASCADE;
DROP STATISTICS IF EXISTS alterstatistics_00674_stx CASCADE;
DROP OWNED BY alterstatistics_00674_newowner CASCADE;
DROP ROLE IF EXISTS alterstatistics_00674_newowner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterstatistics_00674_newowner LOGIN;
CREATE TABLE alterstatistics_00674_tab (alterstatistics_00674_c1 integer, alterstatistics_00674_c2 integer);
CREATE STATISTICS alterstatistics_00674_stx ON alterstatistics_00674_tab (alterstatistics_00674_c1, alterstatistics_00674_c2);
-- 3. 执行唯一获得覆盖信用的 ALTER STATISTICS。
-- primary-target-begin
ALTER STATISTICS alterstatistics_00674_stx OWNER TO alterstatistics_00674_newowner;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP STATISTICS IF EXISTS alterstatistics_00674_stx CASCADE;
DROP OWNED BY alterstatistics_00674_newowner CASCADE;
DROP ROLE IF EXISTS alterstatistics_00674_newowner;
DROP TABLE IF EXISTS alterstatistics_00674_tab CASCADE;
