-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CALL privilege_context=insufficient_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CALL10042
-- source_md: skills/pg-sql-generation/references/statements/dml/routine/call.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/routine/call.yaml
-- primary_obligation_id: CALL-EXT|10042|returned_rows|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS call_10042_tbl;
DROP PROCEDURE IF EXISTS call_10042_proc;
DROP OWNED BY call_10042_actor CASCADE;
DROP ROLE IF EXISTS call_10042_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE call_10042_actor LOGIN NOSUPERUSER;
CREATE TABLE call_10042_tbl (val int);
CREATE PROCEDURE call_10042_proc(arg1 int DEFAULT 0) LANGUAGE plpgsql AS $$ BEGIN INSERT INTO call_10042_tbl (val) VALUES (arg1); END; $$;
SET ROLE call_10042_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 CALL。
-- primary-target-begin
CALL call_10042_proc();
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS returned_rows_state FROM call_10042_tbl ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP PROCEDURE IF EXISTS call_10042_proc;
DROP OWNED BY call_10042_actor CASCADE;
DROP ROLE IF EXISTS call_10042_actor;
DROP TABLE IF EXISTS call_10042_tbl;
