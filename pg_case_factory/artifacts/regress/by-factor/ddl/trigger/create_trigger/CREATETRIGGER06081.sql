-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TRIGGER duplicate_trigger=without_OR_REPLACE_error
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETRIGGER06081
-- source_md: skills/pg-sql-generation/references/statements/ddl/trigger/create_trigger.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/trigger/create_trigger.yaml
-- primary_obligation_id: CTRG-EXT|06081|information_schema_triggers|DROP_TRIGGER_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42710
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createtrigger_06081_tbl CASCADE;
\set ON_ERROR_STOP on
DROP FUNCTION IF EXISTS createtrigger_06081_fn() CASCADE;
RESET ROLE;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE createtrigger_06081_tbl (id integer, createtrigger_06081_col_a integer);
CREATE FUNCTION createtrigger_06081_fn() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END; $$;
CREATE TRIGGER createtrigger_06081_trig AFTER UPDATE ON createtrigger_06081_tbl FOR EACH ROW EXECUTE FUNCTION createtrigger_06081_fn();
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE TRIGGER。
-- primary-target-begin
CREATE CONSTRAINT TRIGGER createtrigger_06081_trig AFTER UPDATE ON createtrigger_06081_tbl REFERENCING OLD TABLE AS createtrigger_06081_old_rows NEW TABLE AS createtrigger_06081_new_rows FOR EACH ROW EXECUTE FUNCTION createtrigger_06081_fn();
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42710' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS trigger_state FROM information_schema.triggers WHERE trigger_name = 'createtrigger_06081_trig' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TRIGGER IF EXISTS createtrigger_06081_trig ON createtrigger_06081_tbl;
DROP FUNCTION IF EXISTS createtrigger_06081_fn() CASCADE;
DROP TABLE IF EXISTS createtrigger_06081_tbl CASCADE;
