-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP TRIGGER object_state=exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPTRIGGER00806
-- source_md: skills/pg-sql-generation/references/statements/ddl/trigger/drop_trigger.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/trigger/drop_trigger.yaml
-- primary_obligation_id: DROPTRIGGER-EXT|00806|drop_trigger|pg_trigger_catalog_query|DROP_TRIGGER_if_exists_cascade
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS droptrigger_00806_t CASCADE;
DROP FUNCTION IF EXISTS droptrigger_00806_fn() CASCADE;
DROP VIEW IF EXISTS droptrigger_00806_depv CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地触发器和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE TABLE droptrigger_00806_t (c integer);
CREATE FUNCTION droptrigger_00806_fn() RETURNS trigger LANGUAGE plpgsql AS $$ BEGIN RETURN NULL; END; $$;
CREATE TRIGGER droptrigger_00806_trg BEFORE INSERT ON droptrigger_00806_t FOR EACH ROW EXECUTE FUNCTION droptrigger_00806_fn();
CREATE VIEW droptrigger_00806_depv AS SELECT * FROM droptrigger_00806_t;
-- 3. 执行唯一获得覆盖信用的 DROP TRIGGER。
-- primary-target-begin
DROP TRIGGER IF EXISTS droptrigger_00806_trg ON "droptrigger_00806_qt" CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS trigger_absent FROM pg_catalog.pg_trigger WHERE tgname = 'droptrigger_00806_trg' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP TRIGGER IF EXISTS droptrigger_00806_trg ON droptrigger_00806_t;
DROP FUNCTION IF EXISTS droptrigger_00806_fn() CASCADE;
DROP VIEW IF EXISTS droptrigger_00806_depv CASCADE;
DROP TABLE IF EXISTS droptrigger_00806_t CASCADE;
