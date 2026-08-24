-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : EXECUTE target_form=execute_statement
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: EXECUTE01200
-- source_md: skills/pg-sql-generation/references/statements/prepared/prepared_statement/execute.md
-- factor_md: skills/pg-sql-generation/references/combinations/prepared/prepared_statement/execute.yaml
-- primary_obligation_id: EXECUTE-EXT|01200|effect_query|reset_state|argument_shape
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS execute_01200_bt CASCADE;
DEALLOCATE ALL;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE execute_01200_bt (c1 int, c2 text);
INSERT INTO execute_01200_bt VALUES (1, 'hello');
PREPARE execute_01200_stmt AS SELECT * FROM execute_01200_bt;
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 EXECUTE。
-- primary-target-begin
EXECUTE execute_01200_stmt;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS row_count FROM execute_01200_bt ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DEALLOCATE ALL;
DROP TABLE IF EXISTS execute_01200_bt CASCADE;
DROP TABLE IF EXISTS execute_01200_bt CASCADE;
