-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER GROUP cross-factor extension: statement_branch=branch_add_user x verification_mode=pg_authid_catalog x cleanup_mode=grant_membership
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERGROUP1205
-- source_md: skills/pg-sql-generation/references/statements/ddl/group/alter_group.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/group/alter_group.yaml
-- primary_obligation_id: AG-EXT|1205|add_user|pg_authid_catalog|grant_membership
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ROLE IF EXISTS altergroup_1205_grp;
DROP ROLE IF EXISTS "altergroup_1205_Usr";
DROP ROLE IF EXISTS "altergroup_1205_Usr2";
\set ON_ERROR_STOP on
-- 2. 创建完整本地角色和因子专用夹具。
CREATE ROLE altergroup_1205_grp;
CREATE ROLE "altergroup_1205_Usr";
CREATE ROLE "altergroup_1205_Usr2";
GRANT altergroup_1205_grp TO "altergroup_1205_Usr";
GRANT altergroup_1205_grp TO "altergroup_1205_Usr2";
-- 3. 执行唯一获得覆盖信用的 ALTER GROUP。
-- primary-target-begin
ALTER GROUP altergroup_1205_grp ADD USER "altergroup_1205_Usr", "altergroup_1205_Usr2";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT rolname FROM pg_catalog.pg_authid WHERE rolname = 'altergroup_1205_grp' ORDER BY oid;
-- 5. 清理全部本编号对象。
ALTER GROUP altergroup_1205_grp ADD USER "altergroup_1205_Usr";
DROP ROLE IF EXISTS altergroup_1205_grp;
DROP ROLE IF EXISTS "altergroup_1205_Usr";
DROP ROLE IF EXISTS "altergroup_1205_Usr2";
