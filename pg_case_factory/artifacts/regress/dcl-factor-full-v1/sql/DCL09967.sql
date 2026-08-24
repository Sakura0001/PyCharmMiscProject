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
-- factor grantee_shape=role_name
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=member_role
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS "dcl_09967_Grantee";
DROP ROLE IF EXISTS dcl_09967_grantor;
DROP ROLE IF EXISTS dcl_09967_member;
CREATE ROLE "dcl_09967_Grantee";
CREATE ROLE dcl_09967_grantor;
CREATE ROLE dcl_09967_member;
DROP FUNCTION IF EXISTS dcl_09967_function(integer);
CREATE FUNCTION dcl_09967_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
GRANT EXECUTE ON FUNCTION dcl_09967_function(integer) TO "dcl_09967_Grantee";
GRANT EXECUTE ON FUNCTION dcl_09967_function(integer) TO dcl_09967_grantor WITH GRANT OPTION;
SET ROLE dcl_09967_grantor;
REVOKE EXECUTE ON FUNCTION dcl_09967_function(integer) FROM "dcl_09967_Grantee" RESTRICT;
RESET ROLE;
SELECT has_function_privilege(CURRENT_USER, 'dcl_09967_function(integer)', 'EXECUTE');
RESET ROLE;
RESET ALL;
DROP FUNCTION IF EXISTS dcl_09967_function(integer);
DROP OWNED BY "dcl_09967_Grantee";
DROP OWNED BY dcl_09967_member;
DROP OWNED BY dcl_09967_grantor;
DROP ROLE IF EXISTS dcl_09967_member;
DROP ROLE IF EXISTS dcl_09967_grantor;
DROP ROLE IF EXISTS "dcl_09967_Grantee";
