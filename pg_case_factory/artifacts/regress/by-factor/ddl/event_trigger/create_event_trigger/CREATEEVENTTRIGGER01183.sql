-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE EVENT TRIGGER trigger_function_state=function_exists_wrong_return_type
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEEVENTTRIGGER01183
-- source_md: skills/pg-sql-generation/references/statements/ddl/event_trigger/create_event_trigger.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/event_trigger/create_event_trigger.yaml
-- primary_obligation_id: CET-EXT|01183|error_assertion|drop_function
-- expected_outcome: expected_failure
-- expected_sqlstate: 42804
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP EVENT TRIGGER IF EXISTS createeventtrigger_01183_trig;
DROP FUNCTION IF EXISTS createeventtrigger_01183_evtfn;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FUNCTION createeventtrigger_01183_evtfn() RETURNS text LANGUAGE plpgsql AS $$ BEGIN END; $$;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE EVENT TRIGGER。
-- primary-target-begin
CREATE EVENT TRIGGER createeventtrigger_01183_trig ON ddl_command_end WHEN TAG IN ('ALTER TABLE') AND TAG IN ('CREATE TABLE') EXECUTE PROCEDURE createeventtrigger_01183_evtfn();
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42804' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP EVENT TRIGGER IF EXISTS createeventtrigger_01183_trig;
DROP FUNCTION IF EXISTS createeventtrigger_01183_evtfn;
