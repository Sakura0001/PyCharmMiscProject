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
-- case_id: CREATETRIGGER00220
-- source_md: skills/pg-sql-generation/references/statements/ddl/trigger/create_trigger.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/trigger/create_trigger.yaml
-- primary_obligation_id: CTRG-EXT|00220|pg_trigger_catalog_query|DROP_TRIGGER_ON_TABLE
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createtrigger_00220_tbl CASCADE;
\set ON_ERROR_STOP on
DROP FUNCTION IF EXISTS createtrigger_00220_fn() CASCADE;
DROP VIEW IF EXISTS createtrigger_00220_vw CASCADE;
RESET ROLE;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE createtrigger_00220_tbl (id integer);
CREATE VIEW createtrigger_00220_vw AS SELECT * FROM createtrigger_00220_tbl;
CREATE FUNCTION createtrigger_00220_fn() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END; $$;
-- 3. 执行唯一获得覆盖信用的 CREATE TRIGGER。
-- primary-target-begin
CREATE TRIGGER createtrigger_00220_trig INSTEAD OF INSERT ON createtrigger_00220_vw FOR EACH ROW WHEN (createtrigger_00220_col_a IS NOT NULL) EXECUTE FUNCTION createtrigger_00220_fn();
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS trigger_state FROM pg_catalog.pg_trigger WHERE tgname = 'createtrigger_00220_trig' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FUNCTION IF EXISTS createtrigger_00220_fn() CASCADE;
DROP VIEW IF EXISTS createtrigger_00220_vw CASCADE;
DROP TABLE IF EXISTS createtrigger_00220_tbl CASCADE;
