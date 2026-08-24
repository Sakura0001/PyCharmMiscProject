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
-- factor grantee_shape=current_role
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=none
-- factor ownership_boundary=owner
-- factor verification_mode=returned_rows
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS dcl_09984_grantee;
DROP ROLE IF EXISTS dcl_09984_grantor;
DROP ROLE IF EXISTS dcl_09984_member;
CREATE ROLE dcl_09984_grantee;
CREATE ROLE dcl_09984_grantor;
CREATE ROLE dcl_09984_member;
DROP FUNCTION IF EXISTS dcl_09984_function(integer);
CREATE FUNCTION dcl_09984_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
GRANT EXECUTE ON FUNCTION dcl_09984_function(integer) TO CURRENT_ROLE;
REVOKE GRANT OPTION FOR EXECUTE ON FUNCTION dcl_09984_function(integer) FROM CURRENT_ROLE GRANTED BY dcl_09984_grantor RESTRICT;
SELECT 'revoke' AS completed_statement, 'routine_language_type_fdw_server' AS privilege_scope;
DROP FUNCTION IF EXISTS dcl_09984_function(integer);
DROP OWNED BY dcl_09984_grantee;
DROP OWNED BY dcl_09984_member;
DROP OWNED BY dcl_09984_grantor;
DROP ROLE IF EXISTS dcl_09984_member;
DROP ROLE IF EXISTS dcl_09984_grantor;
DROP ROLE IF EXISTS dcl_09984_grantee;
