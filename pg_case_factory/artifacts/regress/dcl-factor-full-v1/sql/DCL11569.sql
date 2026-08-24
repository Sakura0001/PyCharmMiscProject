-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_11 (parameter) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_11
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=current_user
-- factor grant_option_shape=admin_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=missing_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=returned_rows
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_11569_grantor;
DROP ROLE IF EXISTS dcl_11569_member;
CREATE ROLE dcl_11569_grantor;
CREATE ROLE dcl_11569_member;
GRANT SELECT ON PARAMETER work_mem TO CURRENT_USER;
GRANT SELECT ON PARAMETER work_mem TO dcl_11569_grantor WITH GRANT OPTION;
GRANT dcl_11569_grantor TO dcl_11569_member WITH SET TRUE;
SET ROLE dcl_11569_member;
SET ROLE dcl_11569_grantor;
REVOKE ADMIN OPTION FOR SELECT ON PARAMETER work_mem FROM CURRENT_USER RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'routine_language_type_fdw_server' AS privilege_scope;
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_11569_member;
DROP OWNED BY dcl_11569_grantor;
DROP ROLE IF EXISTS dcl_11569_member;
DROP ROLE IF EXISTS dcl_11569_grantor;
