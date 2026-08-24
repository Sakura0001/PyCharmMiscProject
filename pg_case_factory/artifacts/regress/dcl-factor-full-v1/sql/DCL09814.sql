-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_7 (foreign_server) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_7
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=current_role
-- factor grant_option_shape=grant_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=missing_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=error_assertion
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_09814_grantor;
DROP ROLE IF EXISTS dcl_09814_member;
CREATE ROLE dcl_09814_grantor;
CREATE ROLE dcl_09814_member;
DROP SERVER IF EXISTS dcl_09814_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09814_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_09814_fdw;
CREATE SERVER dcl_09814_server FOREIGN DATA WRAPPER dcl_09814_fdw;
GRANT USAGE ON FOREIGN SERVER dcl_09814_missing_object TO CURRENT_ROLE;
GRANT USAGE ON FOREIGN SERVER dcl_09814_missing_object TO dcl_09814_grantor WITH GRANT OPTION;
GRANT dcl_09814_grantor TO dcl_09814_member WITH SET TRUE;
SET ROLE dcl_09814_member;
SET ROLE dcl_09814_grantor;
REVOKE GRANT OPTION FOR USAGE ON FOREIGN SERVER dcl_09814_missing_object FROM CURRENT_ROLE RESTRICT;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
RESET ROLE;
RESET ALL;
DROP SERVER IF EXISTS dcl_09814_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09814_fdw CASCADE;
DROP OWNED BY dcl_09814_member;
DROP OWNED BY dcl_09814_grantor;
DROP ROLE IF EXISTS dcl_09814_member;
DROP ROLE IF EXISTS dcl_09814_grantor;
