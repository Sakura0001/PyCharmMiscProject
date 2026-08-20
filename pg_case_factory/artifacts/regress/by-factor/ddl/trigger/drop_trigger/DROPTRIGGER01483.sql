-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP TRIGGER table_dependency=table_not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPTRIGGER01483
-- source_md: skills/pg-sql-generation/references/statements/ddl/trigger/drop_trigger.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/trigger/drop_trigger.yaml
-- primary_obligation_id: DROPTRIGGER-EXT|01483|drop_trigger|pg_trigger_catalog_query|DROP_TRIGGER_cascade
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P01
-- 1. 清理本编号对象，保证脚本可重复执行。
SELECT 1 AS residual_check_no_objects;
\set ON_ERROR_STOP on
-- 2. 创建完整本地触发器和因子专用夹具。
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP TRIGGER。
-- primary-target-begin
DROP TRIGGER IF EXISTS "select" ON droptrigger_01483_t CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42P01' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS trigger_absent FROM pg_catalog.pg_trigger WHERE tgname = 'select' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
SELECT 1 AS residual_check_no_objects;
