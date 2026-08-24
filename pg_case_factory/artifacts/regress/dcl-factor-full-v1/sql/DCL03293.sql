-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_8 (routine) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_8
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
-- factor grantee_shape=public
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
DROP ROLE IF EXISTS dcl_03293_grantee;
DROP ROLE IF EXISTS dcl_03293_grantor;
DROP ROLE IF EXISTS dcl_03293_member;
CREATE ROLE dcl_03293_grantee;
CREATE ROLE dcl_03293_grantor;
CREATE ROLE dcl_03293_member;
DROP FUNCTION IF EXISTS dcl_03293_function(integer);
CREATE FUNCTION dcl_03293_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
BEGIN;
SET ROLE dcl_03293_grantee;
GRANT EXECUTE ON FUNCTION dcl_03293_missing_object(integer) TO PUBLIC WITH INHERIT TRUE GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'column_privilege' AS privilege_scope;
ROLLBACK;
DROP FUNCTION IF EXISTS dcl_03293_function(integer);
DROP OWNED BY dcl_03293_grantee;
DROP OWNED BY dcl_03293_member;
DROP OWNED BY dcl_03293_grantor;
DROP ROLE IF EXISTS dcl_03293_member;
DROP ROLE IF EXISTS dcl_03293_grantor;
DROP ROLE IF EXISTS dcl_03293_grantee;
