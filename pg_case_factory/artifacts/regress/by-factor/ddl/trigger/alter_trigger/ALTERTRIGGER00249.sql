-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TRIGGER privilege_level=non_owner_no_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTRIGGER00249
-- source_md: skills/pg-sql-generation/references/statements/ddl/trigger/alter_trigger.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/trigger/alter_trigger.yaml
-- primary_obligation_id: ATRG-EXT|00249|pg_trigger_catalog_query|DROP_TRIGGER_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altertrigger_00249_tbl, altertrigger_00249_tbl_part1 CASCADE;
\set ON_ERROR_STOP on
DROP FUNCTION IF EXISTS altertrigger_00249_trigfn() CASCADE;
DROP OWNED BY altertrigger_00249_actor CASCADE;
DROP ROLE IF EXISTS altertrigger_00249_actor;
RESET ROLE;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE altertrigger_00249_actor LOGIN NOSUPERUSER;
CREATE TABLE altertrigger_00249_tbl (id integer) PARTITION BY RANGE (id);
CREATE TABLE altertrigger_00249_tbl_part1 PARTITION OF altertrigger_00249_tbl FOR VALUES FROM (0) TO (100);
CREATE FUNCTION altertrigger_00249_trigfn() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END; $$;
CREATE TRIGGER "altertrigger_00249_MixedTrig" BEFORE INSERT ON altertrigger_00249_tbl FOR EACH ROW EXECUTE FUNCTION altertrigger_00249_trigfn();
SET ROLE altertrigger_00249_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TRIGGER。
-- primary-target-begin
ALTER TRIGGER "altertrigger_00249_MixedTrig" ON altertrigger_00249_tbl RENAME TO "altertrigger_00249_MixedNew";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS trigger_state FROM pg_catalog.pg_trigger WHERE tgname = 'altertrigger_00249_MixedTrig' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TRIGGER IF EXISTS "altertrigger_00249_MixedTrig" ON altertrigger_00249_tbl;
DROP FUNCTION IF EXISTS altertrigger_00249_trigfn() CASCADE;
DROP OWNED BY altertrigger_00249_actor CASCADE;
DROP ROLE IF EXISTS altertrigger_00249_actor;
DROP TABLE IF EXISTS altertrigger_00249_tbl, altertrigger_00249_tbl_part1 CASCADE;
