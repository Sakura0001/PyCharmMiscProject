-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER GROUP cross-factor extension: statement_branch=branch_rename x verification_mode=pg_auth_members_catalog x cleanup_mode=drop_role
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERGROUP3735
-- source_md: skills/pg-sql-generation/references/statements/ddl/group/alter_group.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/group/alter_group.yaml
-- primary_obligation_id: AG-EXT|3735|rename|pg_auth_members_catalog|drop_role
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ROLE IF EXISTS altergroup_3735_grp;
DROP ROLE IF EXISTS "altergroup_3735_Renamed";
DROP ROLE IF EXISTS altergroup_3735_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地角色和因子专用夹具。
CREATE ROLE altergroup_3735_grp;
CREATE ROLE altergroup_3735_actor LOGIN;
SET ROLE altergroup_3735_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER GROUP。
-- primary-target-begin
ALTER GROUP altergroup_3735_grp RENAME TO "altergroup_3735_Renamed";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS rename_source_exists FROM pg_catalog.pg_roles WHERE rolname = 'altergroup_3735_grp' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP ROLE IF EXISTS altergroup_3735_grp;
DROP ROLE IF EXISTS "altergroup_3735_Renamed";
DROP ROLE IF EXISTS altergroup_3735_actor;
