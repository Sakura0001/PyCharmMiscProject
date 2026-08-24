-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER GROUP cross-factor extension: statement_branch=branch_rename x verification_mode=pg_auth_members_catalog x cleanup_mode=grant_membership
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERGROUP3709
-- source_md: skills/pg-sql-generation/references/statements/ddl/group/alter_group.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/group/alter_group.yaml
-- primary_obligation_id: AG-EXT|3709|rename|pg_auth_members_catalog|grant_membership
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ROLE IF EXISTS altergroup_3709_grp;
DROP ROLE IF EXISTS "altergroup_3709_Renamed";
DROP ROLE IF EXISTS altergroup_3709_admin;
\set ON_ERROR_STOP on
-- 2. 创建完整本地角色和因子专用夹具。
CREATE ROLE altergroup_3709_grp;
CREATE ROLE altergroup_3709_admin LOGIN;
GRANT altergroup_3709_grp TO altergroup_3709_admin WITH ADMIN OPTION;
ALTER ROLE altergroup_3709_admin CREATEROLE;
SET ROLE altergroup_3709_admin;
-- 3. 执行唯一获得覆盖信用的 ALTER GROUP。
-- primary-target-begin
ALTER GROUP altergroup_3709_grp RENAME TO "altergroup_3709_Renamed";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS rename_target_exists FROM pg_catalog.pg_roles WHERE rolname = 'altergroup_3709_Renamed' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP ROLE IF EXISTS altergroup_3709_grp;
DROP ROLE IF EXISTS "altergroup_3709_Renamed";
DROP ROLE IF EXISTS altergroup_3709_admin;
