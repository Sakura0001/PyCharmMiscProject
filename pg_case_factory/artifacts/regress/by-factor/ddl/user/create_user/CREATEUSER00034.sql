-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE USER referenced_role_existence=role_not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEUSER00034
-- source_md: skills/pg-sql-generation/references/statements/ddl/user/create_user.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/user/create_user.yaml
-- primary_obligation_id: CU-SFV|sfv-26240c4f1ac08c2b76abd2a5|create_user_branch_1
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ROLE IF EXISTS createuser_00034_user CASCADE;
DROP ROLE IF EXISTS createuser_00034_ref CASCADE;
DROP ROLE IF EXISTS createuser_00034_ref1 CASCADE;
DROP ROLE IF EXISTS createuser_00034_ref2 CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地规则和因子专用夹具。
\set ON_ERROR_STOP off
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 CREATE USER。
-- primary-target-begin
CREATE USER createuser_00034_user WITH IN ROLE createuser_00034_ref;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS role_state FROM pg_catalog.pg_roles WHERE rolname = 'createuser_00034_user' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP USER IF EXISTS createuser_00034_user;
DROP ROLE IF EXISTS createuser_00034_ref;
SELECT 1 AS residual_check_no_objects;
