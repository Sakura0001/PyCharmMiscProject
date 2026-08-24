-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_8 (routine) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_8
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=session_user
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=returned_rows
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_03509_grantee;
DROP ROLE IF EXISTS dcl_03509_grantor;
DROP ROLE IF EXISTS dcl_03509_member;
CREATE ROLE dcl_03509_grantee;
CREATE ROLE dcl_03509_grantor;
CREATE ROLE dcl_03509_member;
DROP FUNCTION IF EXISTS dcl_03509_function(integer);
CREATE FUNCTION dcl_03509_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
BEGIN;
SET ROLE dcl_03509_grantee;
GRANT EXECUTE ON FUNCTION dcl_03509_missing_object(integer) TO SESSION_USER WITH INHERIT TRUE GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'role_membership' AS privilege_scope;
ROLLBACK;
DROP FUNCTION IF EXISTS dcl_03509_function(integer);
DROP OWNED BY dcl_03509_grantee;
DROP OWNED BY dcl_03509_member;
DROP OWNED BY dcl_03509_grantor;
DROP ROLE IF EXISTS dcl_03509_member;
DROP ROLE IF EXISTS dcl_03509_grantor;
DROP ROLE IF EXISTS dcl_03509_grantee;
