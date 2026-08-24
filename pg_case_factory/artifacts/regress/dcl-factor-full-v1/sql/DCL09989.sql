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
-- factor grantee_shape=current_user
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=member_role
-- factor verification_mode=effect_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS "dcl_09989_Grantee";
DROP ROLE IF EXISTS dcl_09989_grantor;
DROP ROLE IF EXISTS dcl_09989_member;
CREATE ROLE "dcl_09989_Grantee";
CREATE ROLE dcl_09989_grantor;
CREATE ROLE dcl_09989_member;
DROP FUNCTION IF EXISTS dcl_09989_function(integer);
CREATE FUNCTION dcl_09989_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
GRANT EXECUTE ON FUNCTION dcl_09989_function(integer) TO CURRENT_USER;
GRANT EXECUTE ON FUNCTION dcl_09989_function(integer) TO dcl_09989_grantor WITH GRANT OPTION;
BEGIN;
SET ROLE dcl_09989_grantor;
REVOKE GRANT OPTION FOR EXECUTE ON FUNCTION dcl_09989_function(integer) FROM CURRENT_USER GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP FUNCTION IF EXISTS dcl_09989_function(integer);
DROP OWNED BY "dcl_09989_Grantee";
DROP OWNED BY dcl_09989_member;
DROP OWNED BY dcl_09989_grantor;
DROP ROLE IF EXISTS dcl_09989_member;
DROP ROLE IF EXISTS dcl_09989_grantor;
DROP ROLE IF EXISTS "dcl_09989_Grantee";
