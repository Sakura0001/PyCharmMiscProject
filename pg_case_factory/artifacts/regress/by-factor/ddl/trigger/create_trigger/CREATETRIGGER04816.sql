-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TRIGGER target_action=after_trigger
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETRIGGER04816
-- source_md: skills/pg-sql-generation/references/statements/ddl/trigger/create_trigger.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/trigger/create_trigger.yaml
-- primary_obligation_id: CTRG-EXT|04816|SELECT_trigger_test|DROP_TRIGGER_ON_TABLE
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createtrigger_04816_tbl CASCADE;
\set ON_ERROR_STOP on
DROP FUNCTION IF EXISTS createtrigger_04816_fn() CASCADE;
RESET ROLE;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE createtrigger_04816_tbl (id integer, createtrigger_04816_col_a integer);
CREATE FUNCTION createtrigger_04816_fn() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END; $$;
CREATE TRIGGER createtrigger_04816_trig AFTER INSERT ON createtrigger_04816_tbl FOR EACH ROW EXECUTE PROCEDURE createtrigger_04816_fn();
-- 3. 执行唯一获得覆盖信用的 CREATE TRIGGER。
-- primary-target-begin
CREATE OR REPLACE TRIGGER createtrigger_04816_trig AFTER INSERT ON createtrigger_04816_tbl REFERENCING OLD TABLE AS createtrigger_04816_old_rows NEW TABLE AS createtrigger_04816_new_rows FOR EACH ROW WHEN (createtrigger_04816_col_a IS NOT NULL) EXECUTE PROCEDURE createtrigger_04816_fn();
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS trigger_state FROM pg_catalog.pg_trigger WHERE tgname = 'createtrigger_04816_trig' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FUNCTION IF EXISTS createtrigger_04816_fn() CASCADE;
DROP TABLE IF EXISTS createtrigger_04816_tbl CASCADE;
