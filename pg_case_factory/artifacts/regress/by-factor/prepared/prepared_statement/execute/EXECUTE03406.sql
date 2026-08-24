-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : EXECUTE prepared_state=deallocated
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: EXECUTE03406
-- source_md: skills/pg-sql-generation/references/statements/prepared/prepared_statement/execute.md
-- factor_md: skills/pg-sql-generation/references/combinations/prepared/prepared_statement/execute.yaml
-- primary_obligation_id: EXECUTE-EXT|03406|effect_query|rollback|behavior_lifecycle
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS execute_03406_bt CASCADE;
DEALLOCATE ALL;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE execute_03406_bt (c1 int, c2 text);
INSERT INTO execute_03406_bt VALUES (1, 'hello');
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 EXECUTE。
-- primary-target-begin
EXECUTE execute_03406_nonexistent;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS execute_03406_bt CASCADE;
DROP TABLE IF EXISTS execute_03406_bt CASCADE;
