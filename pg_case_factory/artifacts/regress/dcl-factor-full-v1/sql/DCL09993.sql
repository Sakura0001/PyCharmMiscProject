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
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=member_role
-- factor verification_mode=returned_rows
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_09993_Grantee";
DROP ROLE IF EXISTS dcl_09993_grantor;
DROP ROLE IF EXISTS dcl_09993_member;
CREATE ROLE "dcl_09993_Grantee";
CREATE ROLE dcl_09993_grantor;
CREATE ROLE dcl_09993_member;
DROP FUNCTION IF EXISTS dcl_09993_function(integer);
CREATE FUNCTION dcl_09993_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
GRANT EXECUTE ON FUNCTION dcl_09993_function(integer) TO SESSION_USER;
GRANT EXECUTE ON FUNCTION dcl_09993_function(integer) TO dcl_09993_grantor WITH GRANT OPTION;
SET ROLE dcl_09993_grantor;
REVOKE EXECUTE ON FUNCTION dcl_09993_function(integer) FROM SESSION_USER GRANTED BY dcl_09993_grantor RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'routine_language_type_fdw_server' AS privilege_scope;
DROP FUNCTION IF EXISTS dcl_09993_function(integer);
DROP OWNED BY "dcl_09993_Grantee";
DROP OWNED BY dcl_09993_member;
DROP OWNED BY dcl_09993_grantor;
DROP ROLE IF EXISTS dcl_09993_member;
DROP ROLE IF EXISTS dcl_09993_grantor;
DROP ROLE IF EXISTS "dcl_09993_Grantee";
