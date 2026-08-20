-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TRIGGER deferrable_clause=NOT_DEFERRABLE
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETRIGGER00017
-- source_md: skills/pg-sql-generation/references/statements/ddl/trigger/create_trigger.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/trigger/create_trigger.yaml
-- primary_obligation_id: CTRG-SFV|sfv-f886dbf95706e786f38736ea|before_trigger
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createtrigger_00017_tbl CASCADE;
\set ON_ERROR_STOP on
DROP FUNCTION IF EXISTS createtrigger_00017_fn() CASCADE;
RESET ROLE;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE createtrigger_00017_tbl (id integer, createtrigger_00017_col_a integer);
CREATE FUNCTION createtrigger_00017_fn() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END; $$;
-- 3. 执行唯一获得覆盖信用的 CREATE TRIGGER。
-- primary-target-begin
CREATE TRIGGER createtrigger_00017_trig BEFORE INSERT ON createtrigger_00017_tbl NOT DEFERRABLE FOR EACH ROW EXECUTE FUNCTION createtrigger_00017_fn();
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS trigger_state FROM pg_catalog.pg_trigger WHERE tgname = 'createtrigger_00017_trig' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TRIGGER IF EXISTS createtrigger_00017_trig ON createtrigger_00017_tbl;
DROP FUNCTION IF EXISTS createtrigger_00017_fn() CASCADE;
DROP TABLE IF EXISTS createtrigger_00017_tbl CASCADE;
