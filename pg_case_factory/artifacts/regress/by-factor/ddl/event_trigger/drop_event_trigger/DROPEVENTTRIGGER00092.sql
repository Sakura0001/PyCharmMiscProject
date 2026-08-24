-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP EVENT TRIGGER trigger_not_exist_no_if_exists=trigger_not_exists_no_if_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPEVENTTRIGGER00092
-- source_md: skills/pg-sql-generation/references/statements/ddl/event_trigger/drop_event_trigger.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/event_trigger/drop_event_trigger.yaml
-- primary_obligation_id: DROPEVENTTRIGGER-EXT|00092|drop_event_trigger|notice_assertion_if_exists|drop_function
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP EVENT TRIGGER IF EXISTS dropeventtrigger_00092_trig;
DROP FUNCTION IF EXISTS dropeventtrigger_00092_func;
\set ON_ERROR_STOP on
-- 2. 创建完整本地事件触发器和因子专用夹具。
SELECT 1 AS target_event_trigger_intentionally_absent;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP EVENT TRIGGER。
-- primary-target-begin
DROP EVENT TRIGGER dropeventtrigger_00092_trig CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS trigger_absent FROM pg_catalog.pg_event_trigger WHERE evtname = 'dropeventtrigger_00092_trig' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP EVENT TRIGGER IF EXISTS dropeventtrigger_00092_trig;
DROP FUNCTION IF EXISTS dropeventtrigger_00092_func;
