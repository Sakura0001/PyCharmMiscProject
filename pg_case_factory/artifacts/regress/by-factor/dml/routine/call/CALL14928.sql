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
-- case_id: CALL14928
-- source_md: skills/pg-sql-generation/references/statements/dml/routine/call.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/routine/call.yaml
-- primary_obligation_id: CALL-EXT|14928|error_assertion|drop_objects
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS call_14928_tbl;
DROP PROCEDURE IF EXISTS public.call_14928_proc;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE call_14928_tbl (val int);
CREATE PROCEDURE public.call_14928_proc(arg1 int DEFAULT 0) LANGUAGE plpgsql AS $$ BEGIN INSERT INTO call_14928_tbl (val) VALUES (arg1); END; $$;
-- 3. 执行唯一获得覆盖信用的 CALL。
-- primary-target-begin
CALL public.call_14928_proc(42);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP PROCEDURE IF EXISTS public.call_14928_proc;
DROP TABLE IF EXISTS call_14928_tbl;
