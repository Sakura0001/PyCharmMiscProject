-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-19
-- version      : 1.0
-- description  : ALTER GROUP cross-factor extension: statement_branch=branch_drop_user x verification_mode=pg_authid_catalog x cleanup_mode=revoke_membership
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERGROUP1852
-- source_md: skills/pg-sql-generation/references/statements/ddl/group/alter_group.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/group/alter_group.yaml
-- primary_obligation_id: AG-EXT|1852|drop_user|pg_authid_catalog|revoke_membership
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ROLE IF EXISTS altergroup_1852_grp;
DROP ROLE IF EXISTS altergroup_1852_usr;
DROP ROLE IF EXISTS altergroup_1852_admin;
\set ON_ERROR_STOP on
-- 2. 创建完整本地角色和因子专用夹具。
CREATE ROLE altergroup_1852_grp;
CREATE ROLE altergroup_1852_admin LOGIN;
GRANT altergroup_1852_grp TO altergroup_1852_admin WITH ADMIN OPTION;
SET ROLE altergroup_1852_admin;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER GROUP。
-- primary-target-begin
ALTER GROUP altergroup_1852_grp DROP USER altergroup_1852_usr;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT rolname FROM pg_catalog.pg_authid WHERE rolname = 'altergroup_1852_grp' ORDER BY oid;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP ROLE IF EXISTS altergroup_1852_grp;
DROP ROLE IF EXISTS altergroup_1852_usr;
DROP ROLE IF EXISTS altergroup_1852_admin;
