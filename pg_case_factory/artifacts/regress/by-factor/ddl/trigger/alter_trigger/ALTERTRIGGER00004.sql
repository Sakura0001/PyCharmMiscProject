-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TRIGGER cleanup_mode=DROP_TRIGGER_IF_EXISTS
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTRIGGER00004
-- source_md: skills/pg-sql-generation/references/statements/ddl/trigger/alter_trigger.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/trigger/alter_trigger.yaml
-- primary_obligation_id: ATRG-SFV|sfv-f390f8197e16a41deda6a87a|rename
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altertrigger_00004_tbl CASCADE;
\set ON_ERROR_STOP on
DROP FUNCTION IF EXISTS altertrigger_00004_trigfn() CASCADE;
RESET ROLE;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE altertrigger_00004_tbl (id integer);
CREATE FUNCTION altertrigger_00004_trigfn() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END; $$;
CREATE TRIGGER altertrigger_00004_trig BEFORE INSERT ON altertrigger_00004_tbl FOR EACH ROW EXECUTE FUNCTION altertrigger_00004_trigfn();
-- 3. 执行唯一获得覆盖信用的 ALTER TRIGGER。
-- primary-target-begin
ALTER TRIGGER altertrigger_00004_trig ON altertrigger_00004_tbl RENAME TO altertrigger_00004_newtrig;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS trigger_state FROM pg_catalog.pg_trigger WHERE tgname = 'altertrigger_00004_newtrig' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TRIGGER IF EXISTS altertrigger_00004_trig ON altertrigger_00004_tbl;
DROP FUNCTION IF EXISTS altertrigger_00004_trigfn() CASCADE;
DROP TABLE IF EXISTS altertrigger_00004_tbl CASCADE;
