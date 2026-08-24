-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CALL condition_shape=join_or_match_condition
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CALL00006
-- source_md: skills/pg-sql-generation/references/statements/dml/routine/call.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/routine/call.yaml
-- primary_obligation_id: CALL-SFV|sfv-ed74471cda079cb3055e6c1c|call
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS call_00006_tbl;
DROP PROCEDURE IF EXISTS call_00006_proc;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE call_00006_tbl (val int);
CREATE PROCEDURE call_00006_proc(arg1 int DEFAULT 0) LANGUAGE plpgsql AS $$ BEGIN INSERT INTO call_00006_tbl (val) VALUES (arg1); END; $$;
-- 3. 执行唯一获得覆盖信用的 CALL。
-- primary-target-begin
CALL call_00006_proc(42);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS effect_state FROM call_00006_tbl ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP PROCEDURE IF EXISTS call_00006_proc;
DROP TABLE IF EXISTS call_00006_tbl;
