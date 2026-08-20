-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ANALYZE target_state=target_missing
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ANALYZE00637
-- source_md: skills/pg-sql-generation/references/statements/utility/statistics/analyze.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/statistics/analyze.yaml
-- primary_obligation_id: ANALYZE-EXT|00637|catalog_query|rollback
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ROLE IF EXISTS analyze_00637_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE analyze_00637_actor LOGIN NOSUPERUSER;
SELECT 1 AS target_table_intentionally_absent;
GRANT MAINTAIN ON analyze_00637_t TO analyze_00637_actor;
SET ROLE analyze_00637_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ANALYZE。
-- primary-target-begin
ANALYZE (VERBOSE) public.analyze_00637_t;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42P01' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS table_absent FROM pg_catalog.pg_class WHERE relname = 'analyze_00637_t' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
ROLLBACK;
DROP ROLE IF EXISTS analyze_00637_actor;
