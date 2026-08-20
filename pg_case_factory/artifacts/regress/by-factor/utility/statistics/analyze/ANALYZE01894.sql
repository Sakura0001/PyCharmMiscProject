-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ANALYZE privilege_context=insufficient_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ANALYZE01894
-- source_md: skills/pg-sql-generation/references/statements/utility/statistics/analyze.md
-- factor_md: skills/pg-sql-generation/references/combinations/utility/statistics/analyze.yaml
-- primary_obligation_id: ANALYZE-EXT|01894|error_assertion|rollback
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS analyze_01894_t;
DROP ROLE IF EXISTS analyze_01894_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE analyze_01894_actor LOGIN NOSUPERUSER;
CREATE TABLE analyze_01894_t (analyze_01894_c int);
INSERT INTO analyze_01894_t VALUES (1), (2), (3);
SET ROLE analyze_01894_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ANALYZE。
-- primary-target-begin
ANALYZE (SKIP_LOCKED) ONLY analyze_01894_t (analyze_01894_c);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
ROLLBACK;
DROP ROLE IF EXISTS analyze_01894_actor;
DROP TABLE IF EXISTS analyze_01894_t;
