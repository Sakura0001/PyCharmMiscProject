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
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=session_user
-- factor grant_option_shape=admin_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=missing_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=returned_rows
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_03445_grantor;
DROP ROLE IF EXISTS dcl_03445_member;
CREATE ROLE dcl_03445_grantor;
CREATE ROLE dcl_03445_member;
DROP FUNCTION IF EXISTS dcl_03445_function(integer);
CREATE FUNCTION dcl_03445_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
GRANT EXECUTE ON FUNCTION dcl_03445_missing_object(integer) TO dcl_03445_grantor WITH GRANT OPTION;
GRANT dcl_03445_grantor TO dcl_03445_member WITH SET TRUE;
SET ROLE dcl_03445_member;
SET ROLE dcl_03445_grantor;
GRANT EXECUTE ON FUNCTION dcl_03445_missing_object(integer) TO SESSION_USER WITH ADMIN OPTION;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'routine_language_type_fdw_server' AS privilege_scope;
RESET ROLE;
RESET ALL;
DROP FUNCTION IF EXISTS dcl_03445_function(integer);
DROP OWNED BY dcl_03445_member;
DROP OWNED BY dcl_03445_grantor;
DROP ROLE IF EXISTS dcl_03445_member;
DROP ROLE IF EXISTS dcl_03445_grantor;
