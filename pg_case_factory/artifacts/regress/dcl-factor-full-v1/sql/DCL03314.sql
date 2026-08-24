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
-- factor grantee_shape=current_user
-- factor grant_option_shape=admin_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=plain_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=error_assertion
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_03314_grantee;
DROP ROLE IF EXISTS dcl_03314_grantor;
DROP ROLE IF EXISTS dcl_03314_member;
CREATE ROLE dcl_03314_grantee;
CREATE ROLE dcl_03314_grantor;
CREATE ROLE dcl_03314_member;
DROP FUNCTION IF EXISTS dcl_03314_function(integer);
CREATE FUNCTION dcl_03314_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
BEGIN;
SET ROLE dcl_03314_grantee;
GRANT EXECUTE ON FUNCTION dcl_03314_missing_object(integer) TO CURRENT_USER WITH ADMIN OPTION GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
ROLLBACK;
DROP FUNCTION IF EXISTS dcl_03314_function(integer);
DROP OWNED BY dcl_03314_grantee;
DROP OWNED BY dcl_03314_member;
DROP OWNED BY dcl_03314_grantor;
DROP ROLE IF EXISTS dcl_03314_member;
DROP ROLE IF EXISTS dcl_03314_grantor;
DROP ROLE IF EXISTS dcl_03314_grantee;
