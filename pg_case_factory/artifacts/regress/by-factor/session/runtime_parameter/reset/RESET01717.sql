-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : RESET target_action=reset
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: RESET01717
-- source_md: skills/pg-sql-generation/references/statements/session/runtime_parameter/reset.md
-- factor_md: skills/pg-sql-generation/references/combinations/session/runtime_parameter/reset.yaml
-- primary_obligation_id: RESET-EXT|01717|error_assertion|reset_state|dependency_invalid
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
ROLLBACK;
RESET ROLE;
RESET work_mem;
DROP ROLE IF EXISTS reset_01717_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
SET work_mem = '64MB';
CREATE ROLE reset_01717_actor LOGIN NOSUPERUSER;
SET ROLE reset_01717_actor;
-- 3. 执行唯一获得覆盖信用的 RESET。
-- primary-target-begin
RESET work_mem;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET work_mem;
RESET ROLE;
DROP OWNED BY reset_01717_actor CASCADE;
DROP ROLE IF EXISTS reset_01717_actor;
