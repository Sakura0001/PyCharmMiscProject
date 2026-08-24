-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TRIGGER privilege_level=non_owner_with_create_trigger
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETRIGGER00048
-- source_md: skills/pg-sql-generation/references/statements/ddl/trigger/create_trigger.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/trigger/create_trigger.yaml
-- primary_obligation_id: CTRG-SFV|sfv-14913ad9f2ed4257b68d2b95|before_trigger
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createtrigger_00048_tbl CASCADE;
\set ON_ERROR_STOP on
DROP FUNCTION IF EXISTS createtrigger_00048_fn() CASCADE;
DROP OWNED BY createtrigger_00048_actor CASCADE;
DROP ROLE IF EXISTS createtrigger_00048_actor;
RESET ROLE;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createtrigger_00048_actor LOGIN NOSUPERUSER;
GRANT CREATE ON SCHEMA public TO createtrigger_00048_actor;
GRANT USAGE ON SCHEMA public TO createtrigger_00048_actor;
CREATE TABLE createtrigger_00048_tbl (id integer, createtrigger_00048_col_a integer);
CREATE FUNCTION createtrigger_00048_fn() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END; $$;
SET ROLE createtrigger_00048_actor;
-- 3. 执行唯一获得覆盖信用的 CREATE TRIGGER。
-- primary-target-begin
CREATE TRIGGER createtrigger_00048_trig BEFORE INSERT ON createtrigger_00048_tbl FOR EACH ROW EXECUTE FUNCTION createtrigger_00048_fn();
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS trigger_state FROM pg_catalog.pg_trigger WHERE tgname = 'createtrigger_00048_trig' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TRIGGER IF EXISTS createtrigger_00048_trig ON createtrigger_00048_tbl;
DROP FUNCTION IF EXISTS createtrigger_00048_fn() CASCADE;
DROP OWNED BY createtrigger_00048_actor CASCADE;
DROP ROLE IF EXISTS createtrigger_00048_actor;
DROP TABLE IF EXISTS createtrigger_00048_tbl CASCADE;
