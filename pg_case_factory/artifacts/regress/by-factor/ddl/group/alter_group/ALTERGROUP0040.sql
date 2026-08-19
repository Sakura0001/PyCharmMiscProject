-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER GROUP rename_to_existing_name=same_name_conflict
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERGROUP0040
-- source_md: skills/pg-sql-generation/references/statements/ddl/group/alter_group.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/group/alter_group.yaml
-- primary_obligation_id: AG-SFV|sfv-5bf47f5a28508df0862d1e32|rename
-- expected_outcome: expected_failure
-- expected_sqlstate: 42710
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ROLE IF EXISTS altergroup_0040_grp;
DROP ROLE IF EXISTS altergroup_0040_conflict_grp;
DROP ROLE IF EXISTS altergroup_0040_renamed;
DROP ROLE IF EXISTS altergroup_0040_admin;
\set ON_ERROR_STOP on
-- 2. 创建完整本地角色和因子专用夹具。
CREATE ROLE altergroup_0040_grp;
CREATE ROLE altergroup_0040_conflict_grp;
CREATE ROLE altergroup_0040_admin LOGIN;
GRANT altergroup_0040_grp TO altergroup_0040_admin WITH ADMIN OPTION;
ALTER ROLE altergroup_0040_admin CREATEROLE;
SET ROLE altergroup_0040_admin;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER GROUP。
-- primary-target-begin
ALTER GROUP altergroup_0040_grp RENAME TO altergroup_0040_conflict_grp;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42710' AS target_sqlstate_matches_expected;
SELECT EXISTS(SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'altergroup_0040_grp') AS rename_source_exists;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP ROLE IF EXISTS altergroup_0040_grp;
DROP ROLE IF EXISTS altergroup_0040_conflict_grp;
DROP ROLE IF EXISTS altergroup_0040_renamed;
DROP ROLE IF EXISTS altergroup_0040_admin;
