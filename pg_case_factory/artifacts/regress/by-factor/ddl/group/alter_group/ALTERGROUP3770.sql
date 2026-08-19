-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER GROUP cross-factor extension: statement_branch=branch_rename x verification_mode=pg_auth_members_catalog x cleanup_mode=revert_rename
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERGROUP3770
-- source_md: skills/pg-sql-generation/references/statements/ddl/group/alter_group.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/group/alter_group.yaml
-- primary_obligation_id: AG-EXT|3770|rename|pg_auth_members_catalog|revert_rename
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ROLE IF EXISTS "altergroup_3770_Grp";
DROP ROLE IF EXISTS "altergroup_3770_Renamed";
DROP ROLE IF EXISTS altergroup_3770_admin;
\set ON_ERROR_STOP on
-- 2. 创建完整本地角色和因子专用夹具。
CREATE ROLE "altergroup_3770_Grp";
CREATE ROLE altergroup_3770_admin LOGIN;
GRANT "altergroup_3770_Grp" TO altergroup_3770_admin WITH ADMIN OPTION;
ALTER ROLE altergroup_3770_admin CREATEROLE;
SET ROLE altergroup_3770_admin;
-- 3. 执行唯一获得覆盖信用的 ALTER GROUP。
-- primary-target-begin
ALTER GROUP "altergroup_3770_Grp" RENAME TO "altergroup_3770_Renamed";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'altergroup_3770_Renamed') AS rename_target_exists;
-- 5. 清理全部本编号对象。
RESET ROLE;
ALTER GROUP "altergroup_3770_Renamed" RENAME TO "altergroup_3770_Grp";
DROP ROLE IF EXISTS "altergroup_3770_Grp";
DROP ROLE IF EXISTS "altergroup_3770_Renamed";
DROP ROLE IF EXISTS altergroup_3770_admin;
