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
-- case_id: CREATETRIGGER03316
-- source_md: skills/pg-sql-generation/references/statements/ddl/trigger/create_trigger.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/trigger/create_trigger.yaml
-- primary_obligation_id: CTRG-EXT|03316|pg_trigger_catalog_query|DROP_TRIGGER_ON_TABLE
-- expected_outcome: expected_failure
-- expected_sqlstate: 42710
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createtrigger_03316_tbl CASCADE;
\set ON_ERROR_STOP on
DROP FUNCTION IF EXISTS createtrigger_03316_fn() CASCADE;
RESET ROLE;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE createtrigger_03316_tbl (id integer, createtrigger_03316_col_a integer);
CREATE FUNCTION createtrigger_03316_fn() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END; $$;
CREATE TRIGGER createtrigger_03316_trig AFTER UPDATE ON createtrigger_03316_tbl FOR EACH ROW EXECUTE FUNCTION createtrigger_03316_fn();
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE TRIGGER。
-- primary-target-begin
CREATE TRIGGER createtrigger_03316_trig AFTER UPDATE ON createtrigger_03316_tbl REFERENCING OLD TABLE AS createtrigger_03316_old_rows NEW TABLE AS createtrigger_03316_new_rows WHEN (createtrigger_03316_col_a IS NOT NULL) EXECUTE FUNCTION createtrigger_03316_fn();
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42710' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS trigger_state FROM pg_catalog.pg_trigger WHERE tgname = 'createtrigger_03316_trig' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FUNCTION IF EXISTS createtrigger_03316_fn() CASCADE;
DROP TABLE IF EXISTS createtrigger_03316_tbl CASCADE;
