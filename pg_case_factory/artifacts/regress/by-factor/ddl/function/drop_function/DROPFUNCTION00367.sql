-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP FUNCTION object_state=exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPFUNCTION00367
-- source_md: skills/pg-sql-generation/references/statements/ddl/function/drop_function.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/function/drop_function.yaml
-- primary_obligation_id: DROPFUNCTION-EXT|00367|drop_function|pg_proc_catalog_query|DROP_FUNCTION_cascade
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS dropfunction_00367_t CASCADE;
DROP VIEW IF EXISTS dropfunction_00367_v CASCADE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地函数和因子专用夹具。
SELECT 1 AS target_function_intentionally_absent;
CREATE TABLE dropfunction_00367_t (c integer);
CREATE VIEW dropfunction_00367_v AS SELECT dropfunction_00367_fn(c) AS result FROM dropfunction_00367_t;
-- 3. 执行唯一获得覆盖信用的 DROP FUNCTION。
-- primary-target-begin
DROP FUNCTION IF EXISTS dropfunction_00367_fn(integer) CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS function_absent FROM pg_catalog.pg_proc WHERE proname = 'dropfunction_00367_fn' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP VIEW IF EXISTS dropfunction_00367_v CASCADE;
DROP TABLE IF EXISTS dropfunction_00367_t CASCADE;
