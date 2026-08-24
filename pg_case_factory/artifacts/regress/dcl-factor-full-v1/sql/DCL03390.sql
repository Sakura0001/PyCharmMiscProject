-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_8 (routine) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_8
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=session_user
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=quoted_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=error_assertion
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_03390_Grantee";
DROP ROLE IF EXISTS dcl_03390_grantor;
DROP ROLE IF EXISTS dcl_03390_member;
CREATE ROLE "dcl_03390_Grantee";
CREATE ROLE dcl_03390_grantor;
CREATE ROLE dcl_03390_member;
DROP FUNCTION IF EXISTS dcl_03390_function(integer);
CREATE FUNCTION dcl_03390_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
SET ROLE "dcl_03390_Grantee";
GRANT EXECUTE ON FUNCTION dcl_03390_missing_object(integer) TO SESSION_USER WITH INHERIT TRUE GRANTED BY dcl_03390_grantor;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
DROP FUNCTION IF EXISTS dcl_03390_function(integer);
DROP OWNED BY "dcl_03390_Grantee";
DROP OWNED BY dcl_03390_member;
DROP OWNED BY dcl_03390_grantor;
DROP ROLE IF EXISTS dcl_03390_member;
DROP ROLE IF EXISTS dcl_03390_grantor;
DROP ROLE IF EXISTS "dcl_03390_Grantee";
