-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TRIGGER constraint_trigger_on_non_constraint_event=CONSTRAINT_with_INSTEAD_OF
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETRIGGER00014
-- source_md: skills/pg-sql-generation/references/statements/ddl/trigger/create_trigger.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/trigger/create_trigger.yaml
-- primary_obligation_id: CTRG-SFV|sfv-f97ae4da68682004a46c3a82|instead_of_trigger
-- expected_outcome: expected_failure
-- expected_sqlstate: 42609
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createtrigger_00014_tbl CASCADE;
\set ON_ERROR_STOP on
DROP FUNCTION IF EXISTS createtrigger_00014_fn() CASCADE;
DROP VIEW IF EXISTS createtrigger_00014_vw CASCADE;
RESET ROLE;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE createtrigger_00014_tbl (id integer);
CREATE VIEW createtrigger_00014_vw AS SELECT * FROM createtrigger_00014_tbl;
CREATE FUNCTION createtrigger_00014_fn() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END; $$;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE TRIGGER。
-- primary-target-begin
CREATE CONSTRAINT TRIGGER createtrigger_00014_trig INSTEAD OF INSERT ON createtrigger_00014_vw FOR EACH ROW EXECUTE FUNCTION createtrigger_00014_fn();
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42609' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS trigger_state FROM pg_catalog.pg_trigger WHERE tgname = 'createtrigger_00014_trig' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TRIGGER IF EXISTS createtrigger_00014_trig ON createtrigger_00014_vw;
DROP FUNCTION IF EXISTS createtrigger_00014_fn() CASCADE;
DROP VIEW IF EXISTS createtrigger_00014_vw CASCADE;
DROP TABLE IF EXISTS createtrigger_00014_tbl CASCADE;
