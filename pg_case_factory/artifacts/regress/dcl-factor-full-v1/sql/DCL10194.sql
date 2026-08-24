-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_8 (routine) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_8
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=public
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
DROP ROLE IF EXISTS "dcl_10194_Grantee";
DROP ROLE IF EXISTS dcl_10194_grantor;
DROP ROLE IF EXISTS dcl_10194_member;
CREATE ROLE "dcl_10194_Grantee";
CREATE ROLE dcl_10194_grantor;
CREATE ROLE dcl_10194_member;
DROP FUNCTION IF EXISTS dcl_10194_function(integer);
CREATE FUNCTION dcl_10194_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
GRANT EXECUTE ON FUNCTION dcl_10194_missing_object(integer) TO PUBLIC;
SET ROLE "dcl_10194_Grantee";
REVOKE GRANT OPTION FOR EXECUTE ON FUNCTION dcl_10194_missing_object(integer) FROM PUBLIC GRANTED BY dcl_10194_grantor RESTRICT;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
DROP FUNCTION IF EXISTS dcl_10194_function(integer);
DROP OWNED BY "dcl_10194_Grantee";
DROP OWNED BY dcl_10194_member;
DROP OWNED BY dcl_10194_grantor;
DROP ROLE IF EXISTS dcl_10194_member;
DROP ROLE IF EXISTS dcl_10194_grantor;
DROP ROLE IF EXISTS "dcl_10194_Grantee";
