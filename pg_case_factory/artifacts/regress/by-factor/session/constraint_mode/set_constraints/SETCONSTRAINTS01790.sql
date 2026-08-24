-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : SET CONSTRAINTS target_action=set_constraints
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: SETCONSTRAINTS01790
-- source_md: skills/pg-sql-generation/references/statements/session/constraint_mode/set_constraints.md
-- factor_md: skills/pg-sql-generation/references/combinations/session/constraint_mode/set_constraints.yaml
-- primary_obligation_id: SETCONSTRAINTS-EXT|01790|error_assertion|rollback|dependency_invalid
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
ROLLBACK;
RESET ROLE;
RESET work_mem;
DROP ROLE IF EXISTS setconstraints_01790_actor;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
SET work_mem = '64MB';
CREATE ROLE setconstraints_01790_actor LOGIN NOSUPERUSER;
SET ROLE setconstraints_01790_actor;
-- 3. 执行唯一获得覆盖信用的 SET CONSTRAINTS。
-- primary-target-begin
SET CONSTRAINTS ALL IMMEDIATE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET work_mem;
RESET ROLE;
DROP OWNED BY setconstraints_01790_actor CASCADE;
DROP ROLE IF EXISTS setconstraints_01790_actor;
