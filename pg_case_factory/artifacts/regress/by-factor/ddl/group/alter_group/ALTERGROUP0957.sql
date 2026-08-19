-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER GROUP cross-factor extension: statement_branch=branch_add_user x verification_mode=error_assertion x cleanup_mode=grant_membership
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERGROUP0957
-- source_md: skills/pg-sql-generation/references/statements/ddl/group/alter_group.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/group/alter_group.yaml
-- primary_obligation_id: AG-EXT|0957|add_user|error_assertion|grant_membership
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ROLE IF EXISTS altergroup_0957_grp;
DROP ROLE IF EXISTS altergroup_0957_usr;
DROP ROLE IF EXISTS altergroup_0957_usr2;
DROP ROLE IF EXISTS altergroup_0957_admin;
\set ON_ERROR_STOP on
-- 2. 创建完整本地角色和因子专用夹具。
CREATE ROLE altergroup_0957_usr;
CREATE ROLE altergroup_0957_usr2;
CREATE ROLE altergroup_0957_admin LOGIN;
SET ROLE altergroup_0957_admin;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER GROUP。
-- primary-target-begin
ALTER GROUP altergroup_0957_grp ADD USER altergroup_0957_usr, altergroup_0957_usr2;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT :'target_sqlstate' AS asserted_sqlstate;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP ROLE IF EXISTS altergroup_0957_grp;
DROP ROLE IF EXISTS altergroup_0957_usr;
DROP ROLE IF EXISTS altergroup_0957_usr2;
DROP ROLE IF EXISTS altergroup_0957_admin;
