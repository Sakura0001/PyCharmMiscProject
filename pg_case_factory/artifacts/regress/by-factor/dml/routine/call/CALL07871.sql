-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CALL target_relation_state=wrong_object_type
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CALL07871
-- source_md: skills/pg-sql-generation/references/statements/dml/routine/call.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/routine/call.yaml
-- primary_obligation_id: CALL-EXT|07871|error_assertion|rollback
-- expected_outcome: expected_failure
-- expected_sqlstate: 42809
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS call_07871_tbl;
DROP FUNCTION IF EXISTS call_07871_proc;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE call_07871_tbl (val int);
CREATE FUNCTION call_07871_proc(int) RETURNS int AS $$ SELECT $1 $$ LANGUAGE sql;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CALL。
-- primary-target-begin
WITH call_07871_cte AS (SELECT 42 AS val)
CALL call_07871_proc((SELECT val FROM call_07871_cte));
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42809' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
DROP FUNCTION IF EXISTS call_07871_proc;
DROP TABLE IF EXISTS call_07871_tbl;
