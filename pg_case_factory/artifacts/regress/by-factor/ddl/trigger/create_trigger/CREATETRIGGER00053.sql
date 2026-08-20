-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TRIGGER referenced_table_not_exists=FROM_table_not_found
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETRIGGER00053
-- source_md: skills/pg-sql-generation/references/statements/ddl/trigger/create_trigger.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/trigger/create_trigger.yaml
-- primary_obligation_id: CTRG-SFV|sfv-483c5d59740c83d0badd9b8e|before_trigger
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createtrigger_00053_tbl, createtrigger_00053_reftbl CASCADE;
\set ON_ERROR_STOP on
DROP FUNCTION IF EXISTS createtrigger_00053_fn() CASCADE;
RESET ROLE;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE createtrigger_00053_tbl (id integer, createtrigger_00053_col_a integer);
CREATE FUNCTION createtrigger_00053_fn() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END; $$;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE TRIGGER。
-- primary-target-begin
CREATE TRIGGER createtrigger_00053_trig BEFORE INSERT ON createtrigger_00053_tbl FROM createtrigger_00053_reftbl FOR EACH ROW EXECUTE FUNCTION createtrigger_00053_fn();
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42P01' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS trigger_state FROM pg_catalog.pg_trigger WHERE tgname = 'createtrigger_00053_trig' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TRIGGER IF EXISTS createtrigger_00053_trig ON createtrigger_00053_tbl;
DROP FUNCTION IF EXISTS createtrigger_00053_fn() CASCADE;
DROP TABLE IF EXISTS createtrigger_00053_tbl, createtrigger_00053_reftbl CASCADE;
