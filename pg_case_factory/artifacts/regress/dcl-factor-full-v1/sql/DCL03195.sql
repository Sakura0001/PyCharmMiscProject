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
-- factor grantee_shape=current_role
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
DROP ROLE IF EXISTS "dcl_03195_Grantee";
DROP ROLE IF EXISTS dcl_03195_grantor;
DROP ROLE IF EXISTS dcl_03195_member;
CREATE ROLE "dcl_03195_Grantee";
CREATE ROLE dcl_03195_grantor;
CREATE ROLE dcl_03195_member;
DROP FUNCTION IF EXISTS dcl_03195_function(integer);
CREATE FUNCTION dcl_03195_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
GRANT EXECUTE ON FUNCTION dcl_03195_function(integer) TO dcl_03195_grantor WITH GRANT OPTION;
SET ROLE dcl_03195_grantor;
GRANT EXECUTE ON FUNCTION dcl_03195_function(integer) TO CURRENT_ROLE GRANTED BY dcl_03195_grantor;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'routine_language_type_fdw_server' AS privilege_scope;
DROP FUNCTION IF EXISTS dcl_03195_function(integer);
DROP OWNED BY "dcl_03195_Grantee";
DROP OWNED BY dcl_03195_member;
DROP OWNED BY dcl_03195_grantor;
DROP ROLE IF EXISTS dcl_03195_member;
DROP ROLE IF EXISTS dcl_03195_grantor;
DROP ROLE IF EXISTS "dcl_03195_Grantee";
