-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_7 (foreign_server) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_7
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=session_user
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=plain_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=error_assertion
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_02930_grantee;
DROP ROLE IF EXISTS dcl_02930_grantor;
DROP ROLE IF EXISTS dcl_02930_member;
CREATE ROLE dcl_02930_grantee;
CREATE ROLE dcl_02930_grantor;
CREATE ROLE dcl_02930_member;
DROP SERVER IF EXISTS dcl_02930_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02930_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_02930_fdw;
CREATE SERVER dcl_02930_server FOREIGN DATA WRAPPER dcl_02930_fdw;
BEGIN;
SET ROLE dcl_02930_grantee;
GRANT USAGE ON FOREIGN SERVER dcl_02930_missing_object TO SESSION_USER GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
ROLLBACK;
DROP SERVER IF EXISTS dcl_02930_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02930_fdw CASCADE;
DROP OWNED BY dcl_02930_grantee;
DROP OWNED BY dcl_02930_member;
DROP OWNED BY dcl_02930_grantor;
DROP ROLE IF EXISTS dcl_02930_member;
DROP ROLE IF EXISTS dcl_02930_grantor;
DROP ROLE IF EXISTS dcl_02930_grantee;
