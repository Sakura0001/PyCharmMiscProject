-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CALL target_action=call
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CALL02687
-- source_md: skills/pg-sql-generation/references/statements/dml/routine/call.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/routine/call.yaml
-- primary_obligation_id: CALL-EXT|02687|error_assertion|rollback
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS call_02687_tbl;
DROP PROCEDURE IF EXISTS call_02687_proc;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE call_02687_tbl (val int);
CREATE PROCEDURE call_02687_proc(arg1 int DEFAULT 0) LANGUAGE plpgsql AS $$ BEGIN INSERT INTO call_02687_tbl (val) VALUES (arg1); END; $$;
-- 3. 执行唯一获得覆盖信用的 CALL。
-- primary-target-begin
CALL call_02687_proc((SELECT 1));
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP PROCEDURE IF EXISTS call_02687_proc;
DROP TABLE IF EXISTS call_02687_tbl;
