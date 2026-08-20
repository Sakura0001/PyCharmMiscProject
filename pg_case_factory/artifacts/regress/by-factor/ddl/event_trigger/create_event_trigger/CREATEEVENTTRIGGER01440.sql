-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE EVENT TRIGGER privilege_level=non_superuser
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEEVENTTRIGGER01440
-- source_md: skills/pg-sql-generation/references/statements/ddl/event_trigger/create_event_trigger.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/event_trigger/create_event_trigger.yaml
-- primary_obligation_id: CET-EXT|01440|catalog_query_pg_event_trigger|drop_event_trigger
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP EVENT TRIGGER IF EXISTS createeventtrigger_01440_trig;
DROP FUNCTION IF EXISTS createeventtrigger_01440_evtfn;
DROP OWNED BY createeventtrigger_01440_actor CASCADE;
DROP ROLE IF EXISTS createeventtrigger_01440_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FUNCTION createeventtrigger_01440_evtfn() RETURNS event_trigger LANGUAGE plpgsql AS $$ BEGIN END; $$;
CREATE ROLE createeventtrigger_01440_actor LOGIN NOSUPERUSER;
SET ROLE createeventtrigger_01440_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE EVENT TRIGGER。
-- primary-target-begin
CREATE EVENT TRIGGER createeventtrigger_01440_trig ON ddl_command_end WHEN TAG IN ('DROP FUNCTION', 'CREATE TABLE') EXECUTE PROCEDURE createeventtrigger_01440_evtfn();
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS trigger_state FROM pg_catalog.pg_event_trigger WHERE evtname = 'createeventtrigger_01440_trig' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP EVENT TRIGGER IF EXISTS createeventtrigger_01440_trig;
DROP FUNCTION IF EXISTS createeventtrigger_01440_evtfn;
DROP OWNED BY createeventtrigger_01440_actor CASCADE;
DROP ROLE IF EXISTS createeventtrigger_01440_actor;
