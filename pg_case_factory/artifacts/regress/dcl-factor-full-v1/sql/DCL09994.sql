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
-- factor expected_status=success
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=session_user
-- factor grant_option_shape=grant_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=none
-- factor ownership_boundary=owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_09994_grantee;
DROP ROLE IF EXISTS dcl_09994_grantor;
DROP ROLE IF EXISTS dcl_09994_member;
CREATE ROLE dcl_09994_grantee;
CREATE ROLE dcl_09994_grantor;
CREATE ROLE dcl_09994_member;
DROP FUNCTION IF EXISTS dcl_09994_function(integer);
CREATE FUNCTION dcl_09994_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
GRANT EXECUTE ON FUNCTION dcl_09994_function(integer) TO SESSION_USER;
REVOKE GRANT OPTION FOR EXECUTE ON FUNCTION dcl_09994_function(integer) FROM SESSION_USER RESTRICT;
SELECT has_function_privilege(CURRENT_USER, 'dcl_09994_function(integer)', 'EXECUTE');
RESET ROLE;
RESET ALL;
DROP FUNCTION IF EXISTS dcl_09994_function(integer);
DROP OWNED BY dcl_09994_grantee;
DROP OWNED BY dcl_09994_member;
DROP OWNED BY dcl_09994_grantor;
DROP ROLE IF EXISTS dcl_09994_member;
DROP ROLE IF EXISTS dcl_09994_grantor;
DROP ROLE IF EXISTS dcl_09994_grantee;
