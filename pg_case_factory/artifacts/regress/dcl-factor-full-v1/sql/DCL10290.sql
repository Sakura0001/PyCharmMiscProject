-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_8 (routine) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_8
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=session_user
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=quoted_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=error_assertion
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_10290_Grantee";
DROP ROLE IF EXISTS dcl_10290_grantor;
DROP ROLE IF EXISTS dcl_10290_member;
CREATE ROLE "dcl_10290_Grantee";
CREATE ROLE dcl_10290_grantor;
CREATE ROLE dcl_10290_member;
DROP FUNCTION IF EXISTS dcl_10290_function(integer);
CREATE FUNCTION dcl_10290_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
GRANT EXECUTE ON FUNCTION dcl_10290_missing_object(integer) TO SESSION_USER;
SET ROLE "dcl_10290_Grantee";
REVOKE GRANT OPTION FOR EXECUTE ON FUNCTION dcl_10290_missing_object(integer) FROM SESSION_USER GRANTED BY dcl_10290_grantor RESTRICT;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
DROP FUNCTION IF EXISTS dcl_10290_function(integer);
DROP OWNED BY "dcl_10290_Grantee";
DROP OWNED BY dcl_10290_member;
DROP OWNED BY dcl_10290_grantor;
DROP ROLE IF EXISTS dcl_10290_member;
DROP ROLE IF EXISTS dcl_10290_grantor;
DROP ROLE IF EXISTS "dcl_10290_Grantee";
