-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP TRIGGER dependent_objects=has_dependents_restrict_blocks
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPTRIGGER00009
-- source_md: skills/pg-sql-generation/references/statements/ddl/trigger/drop_trigger.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/trigger/drop_trigger.yaml
-- primary_obligation_id: DROPTRIGGER-SFV|sfv-3e105d0ab5a8c40eec959022|drop_trigger
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS droptrigger_00009_t CASCADE;
DROP FUNCTION IF EXISTS droptrigger_00009_fn() CASCADE;
DROP VIEW IF EXISTS droptrigger_00009_depv CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地触发器和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE TABLE droptrigger_00009_t (c integer);
CREATE FUNCTION droptrigger_00009_fn() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NULL; END; $$;
CREATE TRIGGER droptrigger_00009_trg BEFORE INSERT ON droptrigger_00009_t FOR EACH ROW EXECUTE FUNCTION droptrigger_00009_fn();
CREATE VIEW droptrigger_00009_depv AS SELECT * FROM droptrigger_00009_t;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP TRIGGER。
-- primary-target-begin
DROP TRIGGER IF EXISTS droptrigger_00009_trg ON droptrigger_00009_t RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS trigger_present FROM pg_catalog.pg_trigger WHERE tgname = 'droptrigger_00009_trg' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP TRIGGER IF EXISTS droptrigger_00009_trg ON droptrigger_00009_t;
DROP FUNCTION IF EXISTS droptrigger_00009_fn() CASCADE;
DROP VIEW IF EXISTS droptrigger_00009_depv CASCADE;
DROP TABLE IF EXISTS droptrigger_00009_t CASCADE;
