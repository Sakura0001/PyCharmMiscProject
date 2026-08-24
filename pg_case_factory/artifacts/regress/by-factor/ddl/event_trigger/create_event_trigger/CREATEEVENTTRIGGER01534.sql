-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE EVENT TRIGGER trigger_function_state=function_not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEEVENTTRIGGER01534
-- source_md: skills/pg-sql-generation/references/statements/ddl/event_trigger/create_event_trigger.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/event_trigger/create_event_trigger.yaml
-- primary_obligation_id: CET-EXT|01534|error_assertion|drop_function
-- expected_outcome: expected_failure
-- expected_sqlstate: 42883
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP EVENT TRIGGER IF EXISTS createeventtrigger_01534_trig;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE EVENT TRIGGER。
-- primary-target-begin
CREATE EVENT TRIGGER createeventtrigger_01534_trig ON ddl_command_end WHEN TAG IN ('DROP FUNCTION') EXECUTE PROCEDURE createeventtrigger_01534_nonexistfn();
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42883' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP EVENT TRIGGER IF EXISTS createeventtrigger_01534_trig;
