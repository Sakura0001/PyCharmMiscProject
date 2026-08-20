-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER TRIGGER object_state=not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERTRIGGER01089
-- source_md: skills/pg-sql-generation/references/statements/ddl/trigger/alter_trigger.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/trigger/alter_trigger.yaml
-- primary_obligation_id: ATRG-EXT|01089|pg_trigger_catalog_query|DROP_TRIGGER_IF_EXISTS
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS altertrigger_01089_tbl, altertrigger_01089_tbl_part1 CASCADE;
\set ON_ERROR_STOP on
DROP FUNCTION IF EXISTS altertrigger_01089_trigfn() CASCADE;
RESET ROLE;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE altertrigger_01089_tbl (id integer) PARTITION BY RANGE (id);
CREATE TABLE altertrigger_01089_tbl_part1 PARTITION OF altertrigger_01089_tbl FOR VALUES FROM (0) TO (100);
CREATE FUNCTION altertrigger_01089_trigfn() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NEW; END; $$;
SELECT 1 AS target_trigger_intentionally_absent;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER TRIGGER。
-- primary-target-begin
ALTER TRIGGER "altertrigger_01089_MixedTrig" ON altertrigger_01089_tbl RENAME TO "column";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS trigger_state FROM pg_catalog.pg_trigger WHERE tgname = 'altertrigger_01089_MixedTrig' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FUNCTION IF EXISTS altertrigger_01089_trigfn() CASCADE;
DROP TABLE IF EXISTS altertrigger_01089_tbl, altertrigger_01089_tbl_part1 CASCADE;
