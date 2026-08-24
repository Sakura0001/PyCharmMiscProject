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
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=none
-- factor ownership_boundary=owner
-- factor verification_mode=effect_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_09986_grantee;
DROP ROLE IF EXISTS dcl_09986_grantor;
DROP ROLE IF EXISTS dcl_09986_member;
CREATE ROLE dcl_09986_grantee;
CREATE ROLE dcl_09986_grantor;
CREATE ROLE dcl_09986_member;
DROP FUNCTION IF EXISTS dcl_09986_function(integer);
CREATE FUNCTION dcl_09986_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
GRANT EXECUTE ON FUNCTION dcl_09986_function(integer) TO CURRENT_USER;
BEGIN;
REVOKE EXECUTE ON FUNCTION dcl_09986_function(integer) FROM CURRENT_USER GRANTED BY CURRENT_USER RESTRICT;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP FUNCTION IF EXISTS dcl_09986_function(integer);
DROP OWNED BY dcl_09986_grantee;
DROP OWNED BY dcl_09986_member;
DROP OWNED BY dcl_09986_grantor;
DROP ROLE IF EXISTS dcl_09986_member;
DROP ROLE IF EXISTS dcl_09986_grantor;
DROP ROLE IF EXISTS dcl_09986_grantee;
