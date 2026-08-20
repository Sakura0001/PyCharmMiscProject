-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TRIGGER target_action=before_trigger
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETRIGGER03782
-- source_md: skills/pg-sql-generation/references/statements/ddl/trigger/create_trigger.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/trigger/create_trigger.yaml
-- primary_obligation_id: CTRG-EXT|03782|pg_trigger_catalog_query|DROP_TRIGGER
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createtrigger_03782_tbl CASCADE;
\set ON_ERROR_STOP on
DROP FUNCTION IF EXISTS createtrigger_03782_fn() CASCADE;
RESET ROLE;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE createtrigger_03782_tbl (id integer, createtrigger_03782_col_a integer);
CREATE FUNCTION createtrigger_03782_fn() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END; $$;
CREATE TRIGGER createtrigger_03782_trig BEFORE INSERT ON createtrigger_03782_tbl FOR EACH ROW EXECUTE FUNCTION createtrigger_03782_fn();
-- 3. 执行唯一获得覆盖信用的 CREATE TRIGGER。
-- primary-target-begin
CREATE OR REPLACE TRIGGER createtrigger_03782_trig BEFORE INSERT ON createtrigger_03782_tbl WHEN (createtrigger_03782_col_a IS NOT NULL) EXECUTE FUNCTION createtrigger_03782_fn();
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS trigger_state FROM pg_catalog.pg_trigger WHERE tgname = 'createtrigger_03782_trig' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TRIGGER IF EXISTS createtrigger_03782_trig ON createtrigger_03782_tbl;
DROP FUNCTION IF EXISTS createtrigger_03782_fn() CASCADE;
DROP TABLE IF EXISTS createtrigger_03782_tbl CASCADE;
