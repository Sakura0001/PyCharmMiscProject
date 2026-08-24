-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE TRIGGER privilege_level=non_owner_no_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATETRIGGER00047
-- source_md: skills/pg-sql-generation/references/statements/ddl/trigger/create_trigger.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/trigger/create_trigger.yaml
-- primary_obligation_id: CTRG-SFV|sfv-71d316a1969e9460a1bea40c|before_trigger
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS createtrigger_00047_tbl CASCADE;
\set ON_ERROR_STOP on
DROP FUNCTION IF EXISTS createtrigger_00047_fn() CASCADE;
DROP OWNED BY createtrigger_00047_actor CASCADE;
DROP ROLE IF EXISTS createtrigger_00047_actor;
RESET ROLE;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE createtrigger_00047_actor LOGIN NOSUPERUSER;
CREATE TABLE createtrigger_00047_tbl (id integer, createtrigger_00047_col_a integer);
CREATE FUNCTION createtrigger_00047_fn() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END; $$;
SET ROLE createtrigger_00047_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CREATE TRIGGER。
-- primary-target-begin
CREATE TRIGGER createtrigger_00047_trig BEFORE INSERT ON createtrigger_00047_tbl FOR EACH ROW EXECUTE FUNCTION createtrigger_00047_fn();
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS trigger_state FROM pg_catalog.pg_trigger WHERE tgname = 'createtrigger_00047_trig' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TRIGGER IF EXISTS createtrigger_00047_trig ON createtrigger_00047_tbl;
DROP FUNCTION IF EXISTS createtrigger_00047_fn() CASCADE;
DROP OWNED BY createtrigger_00047_actor CASCADE;
DROP ROLE IF EXISTS createtrigger_00047_actor;
DROP TABLE IF EXISTS createtrigger_00047_tbl CASCADE;
