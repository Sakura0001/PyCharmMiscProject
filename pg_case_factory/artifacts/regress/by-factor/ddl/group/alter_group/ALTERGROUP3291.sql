-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER GROUP cross-factor extension: statement_branch=branch_drop_user x verification_mode=pg_auth_members_catalog x cleanup_mode=drop_role
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERGROUP3291
-- source_md: skills/pg-sql-generation/references/statements/ddl/group/alter_group.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/group/alter_group.yaml
-- primary_obligation_id: AG-EXT|3291|drop_user|pg_auth_members_catalog|drop_role
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ROLE IF EXISTS "altergroup_3291_Grp";
DROP ROLE IF EXISTS "altergroup_3291_Usr";
DROP ROLE IF EXISTS "altergroup_3291_Usr2";
DROP ROLE IF EXISTS altergroup_3291_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地角色和因子专用夹具。
CREATE ROLE "altergroup_3291_Grp";
CREATE ROLE "altergroup_3291_Usr";
CREATE ROLE "altergroup_3291_Usr2";
CREATE ROLE altergroup_3291_actor LOGIN;
SET ROLE altergroup_3291_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER GROUP。
-- primary-target-begin
ALTER GROUP "altergroup_3291_Grp" DROP USER "altergroup_3291_Usr", "altergroup_3291_Usr2";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS membership_absent FROM pg_catalog.pg_auth_members m JOIN pg_catalog.pg_roles g ON g.oid = m.roleid JOIN pg_catalog.pg_roles u ON u.oid = m.member WHERE g.rolname = 'altergroup_3291_Grp' AND u.rolname = 'altergroup_3291_Usr' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP ROLE IF EXISTS "altergroup_3291_Grp";
DROP ROLE IF EXISTS "altergroup_3291_Usr";
DROP ROLE IF EXISTS "altergroup_3291_Usr2";
DROP ROLE IF EXISTS altergroup_3291_actor;
