-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TRIGGER referencing_clause=transition_table_on_foreign_table
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETRIGGER00055
-- source_md: skills/pg-sql-generation/references/statements/ddl/trigger/create_trigger.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/trigger/create_trigger.yaml
-- primary_obligation_id: CTRG-SFV|sfv-33cd840dc43693e47ad23434|before_trigger
-- expected_outcome: expected_failure
-- expected_sqlstate: 42609
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createtrigger_00055_tbl CASCADE;
\set ON_ERROR_STOP on
DROP FUNCTION IF EXISTS createtrigger_00055_fn() CASCADE;
DROP FOREIGN TABLE IF EXISTS createtrigger_00055_ft CASCADE;
DROP SERVER IF EXISTS createtrigger_00055_srv CASCADE;
RESET ROLE;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE createtrigger_00055_tbl (id integer);
CREATE EXTENSION IF NOT EXISTS file_fdw;
CREATE SERVER createtrigger_00055_srv FOREIGN DATA WRAPPER file_fdw;
CREATE FOREIGN TABLE createtrigger_00055_ft (id integer) SERVER createtrigger_00055_srv OPTIONS (filename '/tmp/createtrigger_00055_ft.csv');
CREATE FUNCTION createtrigger_00055_fn() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END; $$;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE TRIGGER。
-- primary-target-begin
CREATE TRIGGER createtrigger_00055_trig AFTER INSERT ON createtrigger_00055_ft REFERENCING NEW TABLE AS createtrigger_00055_new_rows FOR EACH ROW EXECUTE FUNCTION createtrigger_00055_fn();
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42609' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS trigger_state FROM pg_catalog.pg_trigger WHERE tgname = 'createtrigger_00055_trig' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TRIGGER IF EXISTS createtrigger_00055_trig ON createtrigger_00055_ft;
DROP FUNCTION IF EXISTS createtrigger_00055_fn() CASCADE;
DROP FOREIGN TABLE IF EXISTS createtrigger_00055_ft CASCADE;
DROP SERVER IF EXISTS createtrigger_00055_srv CASCADE;
DROP TABLE IF EXISTS createtrigger_00055_tbl CASCADE;
