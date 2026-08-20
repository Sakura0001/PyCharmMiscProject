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
-- case_id: CREATETRIGGER05566
-- source_md: skills/pg-sql-generation/references/statements/ddl/trigger/create_trigger.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/trigger/create_trigger.yaml
-- primary_obligation_id: CTRG-EXT|05566|pg_trigger_catalog_query|DROP_TRIGGER_ON_TABLE
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createtrigger_05566_tbl CASCADE;
\set ON_ERROR_STOP on
DROP FUNCTION IF EXISTS createtrigger_05566_fn() CASCADE;
RESET ROLE;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE createtrigger_05566_tbl (id integer, createtrigger_05566_col_a integer);
CREATE FUNCTION createtrigger_05566_fn() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END; $$;
-- 3. 执行唯一获得覆盖信用的 CREATE TRIGGER。
-- primary-target-begin
CREATE OR REPLACE CONSTRAINT TRIGGER createtrigger_05566_trig AFTER INSERT ON createtrigger_05566_tbl REFERENCING OLD TABLE AS createtrigger_05566_old_rows NEW TABLE AS createtrigger_05566_new_rows FOR EACH ROW WHEN (createtrigger_05566_col_a IS NOT NULL) EXECUTE FUNCTION createtrigger_05566_fn();
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS trigger_state FROM pg_catalog.pg_trigger WHERE tgname = 'createtrigger_05566_trig' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FUNCTION IF EXISTS createtrigger_05566_fn() CASCADE;
DROP TABLE IF EXISTS createtrigger_05566_tbl CASCADE;
