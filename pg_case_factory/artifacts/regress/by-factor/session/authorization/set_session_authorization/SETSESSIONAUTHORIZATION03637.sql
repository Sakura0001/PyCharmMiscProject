-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : SET SESSION AUTHORIZATION transaction_visibility=inside_committed_transaction
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: SETSESSIONAUTHORIZATION03637
-- source_md: skills/pg-sql-generation/references/statements/session/authorization/set_session_authorization.md
-- factor_md: skills/pg-sql-generation/references/combinations/session/authorization/set_session_authorization.yaml
-- primary_obligation_id: SETSESSIONAUTHORIZATION-EXT|03637|error_assertion|reset_state|dependency_transaction
-- expected_outcome: expected_failure
-- expected_sqlstate: 25001
-- 1. 清理本编号对象，保证脚本可重复执行。
ROLLBACK;
SET SESSION AUTHORIZATION DEFAULT;
DROP ROLE IF EXISTS setsessionauthorization_03637_witness;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE setsessionauthorization_03637_witness LOGIN;
GRANT setsessionauthorization_03637_witness TO CURRENT_USER;
BEGIN;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信心的 SET SESSION AUTHORIZATION。
-- primary-target-begin
SET SESSION AUTHORIZATION setsessionauthorization_03637_witness;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
ROLLBACK;
SELECT :'target_sqlstate' = '25001' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
ROLLBACK;
SET SESSION AUTHORIZATION DEFAULT;
DROP ROLE IF EXISTS setsessionauthorization_03637_witness;
