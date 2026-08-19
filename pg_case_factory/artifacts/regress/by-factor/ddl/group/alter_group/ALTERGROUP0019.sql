-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER GROUP group_name_shape=quoted_id
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERGROUP0019
-- source_md: skills/pg-sql-generation/references/statements/ddl/group/alter_group.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/group/alter_group.yaml
-- primary_obligation_id: AG-SFV|sfv-98a879768fb90b118a7baed5|add_user
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ROLE IF EXISTS "altergroup_0019_Grp";
DROP ROLE IF EXISTS altergroup_0019_usr;
DROP ROLE IF EXISTS altergroup_0019_admin;
\set ON_ERROR_STOP on
-- 2. 创建完整本地角色和因子专用夹具。
CREATE ROLE "altergroup_0019_Grp";
CREATE ROLE altergroup_0019_usr;
CREATE ROLE altergroup_0019_admin LOGIN;
GRANT "altergroup_0019_Grp" TO altergroup_0019_admin WITH ADMIN OPTION;
SET ROLE altergroup_0019_admin;
-- 3. 执行唯一获得覆盖信用的 ALTER GROUP。
-- primary-target-begin
ALTER GROUP "altergroup_0019_Grp" ADD USER altergroup_0019_usr;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_auth_members m JOIN pg_catalog.pg_roles g ON g.oid = m.roleid JOIN pg_catalog.pg_roles u ON u.oid = m.member WHERE g.rolname = 'altergroup_0019_Grp' AND u.rolname = 'altergroup_0019_usr') AS membership_present;
-- 5. 清理全部本编号对象。
RESET ROLE;
ALTER GROUP "altergroup_0019_Grp" DROP USER altergroup_0019_usr;
DROP ROLE IF EXISTS "altergroup_0019_Grp";
DROP ROLE IF EXISTS altergroup_0019_usr;
DROP ROLE IF EXISTS altergroup_0019_admin;
