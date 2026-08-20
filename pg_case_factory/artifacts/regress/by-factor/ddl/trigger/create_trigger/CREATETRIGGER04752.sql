-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TRIGGER target_action=instead_of_trigger
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETRIGGER04752
-- source_md: skills/pg-sql-generation/references/statements/ddl/trigger/create_trigger.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/trigger/create_trigger.yaml
-- primary_obligation_id: CTRG-EXT|04752|SELECT_trigger_test|DROP_TRIGGER_IF_EXISTS
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createtrigger_04752_tbl CASCADE;
\set ON_ERROR_STOP on
DROP FUNCTION IF EXISTS createtrigger_04752_fn() CASCADE;
DROP VIEW IF EXISTS createtrigger_04752_vw CASCADE;
RESET ROLE;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE createtrigger_04752_tbl (id integer);
CREATE VIEW createtrigger_04752_vw AS SELECT * FROM createtrigger_04752_tbl;
CREATE FUNCTION createtrigger_04752_fn() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END; $$;
CREATE TRIGGER createtrigger_04752_trig INSTEAD OF DELETE ON createtrigger_04752_vw FOR EACH ROW EXECUTE PROCEDURE createtrigger_04752_fn();
-- 3. 执行唯一获得覆盖信用的 CREATE TRIGGER。
-- primary-target-begin
CREATE OR REPLACE TRIGGER createtrigger_04752_trig INSTEAD OF DELETE ON createtrigger_04752_vw FOR EACH ROW EXECUTE PROCEDURE createtrigger_04752_fn();
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS trigger_state FROM pg_catalog.pg_trigger WHERE tgname = 'createtrigger_04752_trig' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TRIGGER IF EXISTS createtrigger_04752_trig ON createtrigger_04752_vw;
DROP FUNCTION IF EXISTS createtrigger_04752_fn() CASCADE;
DROP VIEW IF EXISTS createtrigger_04752_vw CASCADE;
DROP TABLE IF EXISTS createtrigger_04752_tbl CASCADE;
