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
-- case_id: ALTERSTATISTICS00402
-- source_md: skills/pg-sql-generation/references/statements/ddl/statistics/alter_statistics.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/statistics/alter_statistics.yaml
-- primary_obligation_id: ASTAT-EXT|00402|error_assertion|DROP_STATISTICS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterstatistics_00402_tab CASCADE;
DROP STATISTICS IF EXISTS alterstatistics_00402_nostx CASCADE;
DROP OWNED BY alterstatistics_00402_newowner CASCADE;
DROP ROLE IF EXISTS alterstatistics_00402_newowner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE alterstatistics_00402_newowner LOGIN;
CREATE TABLE alterstatistics_00402_tab (alterstatistics_00402_c1 integer, alterstatistics_00402_c2 integer);
SELECT 1 AS target_statistics_intentionally_absent;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER STATISTICS。
-- primary-target-begin
ALTER STATISTICS alterstatistics_00402_nostx OWNER TO alterstatistics_00402_newowner;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP STATISTICS IF EXISTS alterstatistics_00402_nostx CASCADE;
DROP OWNED BY alterstatistics_00402_newowner CASCADE;
DROP ROLE IF EXISTS alterstatistics_00402_newowner;
DROP TABLE IF EXISTS alterstatistics_00402_tab CASCADE;
