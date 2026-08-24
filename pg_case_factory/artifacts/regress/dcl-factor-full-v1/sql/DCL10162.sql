-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_8 (routine) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_8
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=current_user
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=missing_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=error_assertion
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_10162_grantor;
DROP ROLE IF EXISTS dcl_10162_member;
CREATE ROLE dcl_10162_grantor;
CREATE ROLE dcl_10162_member;
DROP FUNCTION IF EXISTS dcl_10162_function(integer);
CREATE FUNCTION dcl_10162_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
GRANT EXECUTE ON FUNCTION dcl_10162_missing_object(integer) TO CURRENT_USER;
GRANT EXECUTE ON FUNCTION dcl_10162_missing_object(integer) TO dcl_10162_grantor WITH GRANT OPTION;
GRANT dcl_10162_grantor TO dcl_10162_member WITH SET TRUE;
SET ROLE dcl_10162_member;
SET ROLE dcl_10162_grantor;
REVOKE INHERIT OPTION FOR EXECUTE ON FUNCTION dcl_10162_missing_object(integer) FROM CURRENT_USER RESTRICT;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
RESET ROLE;
RESET ALL;
DROP FUNCTION IF EXISTS dcl_10162_function(integer);
DROP OWNED BY dcl_10162_member;
DROP OWNED BY dcl_10162_grantor;
DROP ROLE IF EXISTS dcl_10162_member;
DROP ROLE IF EXISTS dcl_10162_grantor;
