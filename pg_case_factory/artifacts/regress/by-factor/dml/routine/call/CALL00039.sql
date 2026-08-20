-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CALL statement_branch=branch_1
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CALL00039
-- source_md: skills/pg-sql-generation/references/statements/dml/routine/call.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/routine/call.yaml
-- primary_obligation_id: CALL-SFV|sfv-314cfbb14daf18a5cf8b4c93|call
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS call_00039_tbl;
DROP PROCEDURE IF EXISTS call_00039_proc;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE call_00039_tbl (val int);
CREATE PROCEDURE call_00039_proc(arg1 int DEFAULT 0) LANGUAGE plpgsql AS $$ BEGIN INSERT INTO call_00039_tbl (val) VALUES (arg1); END; $$;
-- 3. 执行唯一获得覆盖信用的 CALL。
-- primary-target-begin
CALL call_00039_proc(42);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS effect_state FROM call_00039_tbl ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP PROCEDURE IF EXISTS call_00039_proc;
DROP TABLE IF EXISTS call_00039_tbl;
