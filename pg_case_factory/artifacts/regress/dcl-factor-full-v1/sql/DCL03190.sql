-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_8 (routine) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_8
-- factor expected_status=success
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=public
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
DROP ROLE IF EXISTS dcl_03190_grantee;
DROP ROLE IF EXISTS dcl_03190_grantor;
DROP ROLE IF EXISTS dcl_03190_member;
CREATE ROLE dcl_03190_grantee;
CREATE ROLE dcl_03190_grantor;
CREATE ROLE dcl_03190_member;
DROP FUNCTION IF EXISTS dcl_03190_function(integer);
CREATE FUNCTION dcl_03190_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
GRANT EXECUTE ON FUNCTION dcl_03190_function(integer) TO PUBLIC WITH GRANT OPTION;
SELECT has_function_privilege(CURRENT_USER, 'dcl_03190_function(integer)', 'EXECUTE');
RESET ROLE;
RESET ALL;
DROP FUNCTION IF EXISTS dcl_03190_function(integer);
DROP OWNED BY dcl_03190_grantee;
DROP OWNED BY dcl_03190_member;
DROP OWNED BY dcl_03190_grantor;
DROP ROLE IF EXISTS dcl_03190_member;
DROP ROLE IF EXISTS dcl_03190_grantor;
DROP ROLE IF EXISTS dcl_03190_grantee;
