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
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=returned_rows
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_10157_grantee;
DROP ROLE IF EXISTS dcl_10157_grantor;
DROP ROLE IF EXISTS dcl_10157_member;
CREATE ROLE dcl_10157_grantee;
CREATE ROLE dcl_10157_grantor;
CREATE ROLE dcl_10157_member;
DROP FUNCTION IF EXISTS dcl_10157_function(integer);
CREATE FUNCTION dcl_10157_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
GRANT EXECUTE ON FUNCTION dcl_10157_missing_object(integer) TO CURRENT_USER;
BEGIN;
SET ROLE dcl_10157_grantee;
REVOKE GRANT OPTION FOR EXECUTE ON FUNCTION dcl_10157_missing_object(integer) FROM CURRENT_USER GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'schema_database_tablespace' AS privilege_scope;
ROLLBACK;
DROP FUNCTION IF EXISTS dcl_10157_function(integer);
DROP OWNED BY dcl_10157_grantee;
DROP OWNED BY dcl_10157_member;
DROP OWNED BY dcl_10157_grantor;
DROP ROLE IF EXISTS dcl_10157_member;
DROP ROLE IF EXISTS dcl_10157_grantor;
DROP ROLE IF EXISTS dcl_10157_grantee;
