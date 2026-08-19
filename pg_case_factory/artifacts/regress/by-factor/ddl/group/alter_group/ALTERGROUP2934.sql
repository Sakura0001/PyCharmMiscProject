-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER GROUP cross-factor extension: statement_branch=branch_drop_user x verification_mode=pg_authid_catalog x cleanup_mode=revert_rename
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERGROUP2934
-- source_md: skills/pg-sql-generation/references/statements/ddl/group/alter_group.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/group/alter_group.yaml
-- primary_obligation_id: AG-EXT|2934|drop_user|pg_authid_catalog|revert_rename
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ROLE IF EXISTS altergroup_2934_grp;
DROP ROLE IF EXISTS "altergroup_2934_Usr";
DROP ROLE IF EXISTS "altergroup_2934_Usr2";
\set ON_ERROR_STOP on
-- 2. 创建完整本地角色和因子专用夹具。
CREATE ROLE altergroup_2934_grp;
CREATE ROLE "altergroup_2934_Usr";
CREATE ROLE "altergroup_2934_Usr2";
-- 3. 执行唯一获得覆盖信用的 ALTER GROUP。
-- primary-target-begin
ALTER GROUP altergroup_2934_grp DROP USER "altergroup_2934_Usr", "altergroup_2934_Usr2";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT rolname FROM pg_catalog.pg_authid WHERE rolname = 'altergroup_2934_grp' ORDER BY oid;
-- 5. 清理全部本编号对象。
DROP ROLE IF EXISTS altergroup_2934_grp;
DROP ROLE IF EXISTS "altergroup_2934_Usr";
DROP ROLE IF EXISTS "altergroup_2934_Usr2";
