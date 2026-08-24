-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_8 (routine) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_8
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=session_user
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
DROP ROLE IF EXISTS dcl_03502_grantor;
DROP ROLE IF EXISTS dcl_03502_member;
CREATE ROLE dcl_03502_grantor;
CREATE ROLE dcl_03502_member;
DROP FUNCTION IF EXISTS dcl_03502_function(integer);
CREATE FUNCTION dcl_03502_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
GRANT EXECUTE ON FUNCTION dcl_03502_missing_object(integer) TO dcl_03502_grantor WITH GRANT OPTION;
GRANT dcl_03502_grantor TO dcl_03502_member WITH SET TRUE;
SET ROLE dcl_03502_member;
SET ROLE dcl_03502_grantor;
GRANT EXECUTE ON FUNCTION dcl_03502_missing_object(integer) TO SESSION_USER WITH GRANT OPTION;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
RESET ROLE;
RESET ALL;
DROP FUNCTION IF EXISTS dcl_03502_function(integer);
DROP OWNED BY dcl_03502_member;
DROP OWNED BY dcl_03502_grantor;
DROP ROLE IF EXISTS dcl_03502_member;
DROP ROLE IF EXISTS dcl_03502_grantor;
