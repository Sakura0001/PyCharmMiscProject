-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TRIGGER target_action=rename
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTRIGGER02491
-- source_md: skills/pg-sql-generation/references/statements/ddl/trigger/alter_trigger.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/trigger/alter_trigger.yaml
-- primary_obligation_id: ATRG-EXT|02491|information_schema_triggers|DROP_TRIGGER_IF_EXISTS
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altertrigger_02491_tbl, altertrigger_02491_tbl_part1 CASCADE;
\set ON_ERROR_STOP on
DROP FUNCTION IF EXISTS altertrigger_02491_trigfn() CASCADE;
RESET ROLE;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE altertrigger_02491_tbl (id integer) PARTITION BY RANGE (id);
CREATE TABLE altertrigger_02491_tbl_part1 PARTITION OF altertrigger_02491_tbl FOR VALUES FROM (0) TO (100);
CREATE FUNCTION altertrigger_02491_trigfn() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END; $$;
CREATE TRIGGER altertrigger_02491_trig BEFORE INSERT ON altertrigger_02491_tbl FOR EACH ROW EXECUTE FUNCTION altertrigger_02491_trigfn();
-- 3. 执行唯一获得覆盖信用的 ALTER TRIGGER。
-- primary-target-begin
ALTER TRIGGER altertrigger_02491_trig ON altertrigger_02491_tbl RENAME TO "column";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS trigger_state FROM information_schema.triggers WHERE trigger_name = 'column' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP TRIGGER IF EXISTS altertrigger_02491_trig ON altertrigger_02491_tbl;
DROP FUNCTION IF EXISTS altertrigger_02491_trigfn() CASCADE;
DROP TABLE IF EXISTS altertrigger_02491_tbl, altertrigger_02491_tbl_part1 CASCADE;
