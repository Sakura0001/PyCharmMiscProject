-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP TRIGGER target_trigger_not_exists=without_IF_EXISTS_error
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPTRIGGER00029
-- source_md: skills/pg-sql-generation/references/statements/ddl/trigger/drop_trigger.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/trigger/drop_trigger.yaml
-- primary_obligation_id: DROPTRIGGER-SFV|sfv-2626934934c03b9c0590b167|drop_trigger
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS droptrigger_00029_t CASCADE;
DROP FUNCTION IF EXISTS droptrigger_00029_fn() CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地触发器和因子专用夹具。
SELECT 1 AS setup_boundary;
CREATE TABLE droptrigger_00029_t (c integer);
SELECT 1 AS target_trigger_intentionally_absent;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP TRIGGER。
-- primary-target-begin
DROP TRIGGER droptrigger_00029_trg ON droptrigger_00029_t;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS trigger_absent FROM pg_catalog.pg_trigger WHERE tgname = 'droptrigger_00029_trg' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP TRIGGER IF EXISTS droptrigger_00029_trg ON droptrigger_00029_t;
DROP FUNCTION IF EXISTS droptrigger_00029_fn() CASCADE;
DROP TABLE IF EXISTS droptrigger_00029_t CASCADE;
