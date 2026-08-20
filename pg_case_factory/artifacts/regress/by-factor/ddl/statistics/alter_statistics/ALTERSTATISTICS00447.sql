-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER STATISTICS rename_behavior=rename_to_existing_name_conflict
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERSTATISTICS00447
-- source_md: skills/pg-sql-generation/references/statements/ddl/statistics/alter_statistics.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/statistics/alter_statistics.yaml
-- primary_obligation_id: ASTAT-EXT|00447|error_assertion|DROP_STATISTICS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42710
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterstatistics_00447_tab CASCADE;
DROP STATISTICS IF EXISTS "alterstatistics_00447_Mix Stx" CASCADE;
DROP STATISTICS IF EXISTS alterstatistics_00447_existstx CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE alterstatistics_00447_tab (alterstatistics_00447_c1 integer, alterstatistics_00447_c2 integer);
CREATE STATISTICS "alterstatistics_00447_Mix Stx" ON alterstatistics_00447_tab (alterstatistics_00447_c1, alterstatistics_00447_c2);
CREATE STATISTICS alterstatistics_00447_existstx ON alterstatistics_00447_tab (alterstatistics_00447_c1, alterstatistics_00447_c2);
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER STATISTICS。
-- primary-target-begin
ALTER STATISTICS "alterstatistics_00447_Mix Stx" RENAME TO alterstatistics_00447_existstx;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42710' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP STATISTICS IF EXISTS "alterstatistics_00447_Mix Stx" CASCADE;
DROP STATISTICS IF EXISTS alterstatistics_00447_existstx CASCADE;
DROP TABLE IF EXISTS alterstatistics_00447_tab CASCADE;
