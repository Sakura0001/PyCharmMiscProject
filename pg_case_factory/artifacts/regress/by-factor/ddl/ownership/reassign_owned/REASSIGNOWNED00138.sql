-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : REASSIGN OWNED old_role_identity=role_not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: REASSIGNOWNED00138
-- source_md: skills/pg-sql-generation/references/statements/ddl/ownership/reassign_owned.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/ownership/reassign_owned.yaml
-- primary_obligation_id: REASSIGNOWNED-EXT|00138|reassign_owned|error_assertion|drop_role_cascade
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
SELECT 1 AS residual_check_no_objects;
\set ON_ERROR_STOP on
-- 2. 创建完整本地角色和因子专用夹具。
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 REASSIGN OWNED。
-- primary-target-begin
REASSIGN OWNED BY CURRENT_USER TO reassignowned_00138_new;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT 1 AS error_assertion_oracle;
-- 5. 清理全部本编号对象。
SELECT 1 AS residual_check_no_objects;
