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
-- case_id: DROPTRIGGER00953
-- source_md: skills/pg-sql-generation/references/statements/ddl/trigger/drop_trigger.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/trigger/drop_trigger.yaml
-- primary_obligation_id: DROPTRIGGER-EXT|00953|drop_trigger|information_schema_triggers|DROP_TRIGGER_if_exists_cascade
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS droptrigger_00953_t CASCADE;
DROP FUNCTION IF EXISTS droptrigger_00953_fn() CASCADE;
DROP VIEW IF EXISTS droptrigger_00953_depv CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地触发器和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE TABLE droptrigger_00953_t (c integer);
SELECT 1 AS target_trigger_intentionally_absent;
CREATE VIEW droptrigger_00953_depv AS SELECT * FROM droptrigger_00953_t;
-- 3. 执行唯一获得覆盖信用的 DROP TRIGGER。
-- primary-target-begin
DROP TRIGGER IF EXISTS droptrigger_00953_trg ON droptrigger_00953_t CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS trigger_absent FROM pg_catalog.pg_trigger WHERE tgname = 'droptrigger_00953_trg' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP TRIGGER IF EXISTS droptrigger_00953_trg ON droptrigger_00953_t;
DROP FUNCTION IF EXISTS droptrigger_00953_fn() CASCADE;
DROP VIEW IF EXISTS droptrigger_00953_depv CASCADE;
DROP TABLE IF EXISTS droptrigger_00953_t CASCADE;
