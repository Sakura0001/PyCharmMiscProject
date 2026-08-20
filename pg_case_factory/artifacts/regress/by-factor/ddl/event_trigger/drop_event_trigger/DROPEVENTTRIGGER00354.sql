-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP EVENT TRIGGER object_state=exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPEVENTTRIGGER00354
-- source_md: skills/pg-sql-generation/references/statements/ddl/event_trigger/drop_event_trigger.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/event_trigger/drop_event_trigger.yaml
-- primary_obligation_id: DROPEVENTTRIGGER-EXT|00354|drop_event_trigger|catalog_query_pg_event_trigger_absence|cascade_cleanup
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP EVENT TRIGGER IF EXISTS dropeventtrigger_00354_trig;
DROP FUNCTION IF EXISTS dropeventtrigger_00354_func;
\set ON_ERROR_STOP on
-- 2. 创建完整本地事件触发器和因子专用夹具。
CREATE FUNCTION dropeventtrigger_00354_func() RETURNS event_trigger AS $$ BEGIN END; $$ LANGUAGE plpgsql;
CREATE EVENT TRIGGER dropeventtrigger_00354_trig ON ddl_command_start EXECUTE FUNCTION dropeventtrigger_00354_func();
-- 3. 执行唯一获得覆盖信用的 DROP EVENT TRIGGER。
-- primary-target-begin
DROP EVENT TRIGGER IF EXISTS dropeventtrigger_00354_trig;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS trigger_absent FROM pg_catalog.pg_event_trigger WHERE evtname = 'dropeventtrigger_00354_trig' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP EVENT TRIGGER IF EXISTS dropeventtrigger_00354_trig;
DROP FUNCTION IF EXISTS dropeventtrigger_00354_func;
