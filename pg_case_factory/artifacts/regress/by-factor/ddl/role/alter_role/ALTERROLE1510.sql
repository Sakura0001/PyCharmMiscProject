-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER ROLE cross-factor extension: statement_branch=branch_2_rename x verification_mode=pg_authid_catalog x cleanup_mode=reset_config_parameter
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERROLE1510
-- source_md: skills/pg-sql-generation/references/statements/ddl/role/alter_role.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/role/alter_role.yaml
-- primary_obligation_id: ALTERROLE-EXT|1510|rename|pg_authid_catalog|reset_config_parameter
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ROLE IF EXISTS alterrole_1510_target;
DROP ROLE IF EXISTS "alterrole_1510_from";
DROP ROLE IF EXISTS alterrole_1510_admin;
\set ON_ERROR_STOP on
-- 2. 创建完整本地角色和因子专用夹具。
CREATE ROLE alterrole_1510_target LOGIN;
CREATE ROLE alterrole_1510_admin LOGIN CREATEROLE;
SET ROLE alterrole_1510_admin;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER ROLE。
-- primary-target-begin
ALTER ROLE alterrole_1510_target RENAME TO "alterrole_1510_from";
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT rolname, rolpassword FROM pg_catalog.pg_authid WHERE rolname = 'alterrole_1510_target' ORDER BY oid;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP ROLE IF EXISTS alterrole_1510_target;
DROP ROLE IF EXISTS "alterrole_1510_from";
DROP ROLE IF EXISTS alterrole_1510_admin;
