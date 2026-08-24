-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_8 (routine) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_8
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=current_role
-- factor grant_option_shape=admin_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=returned_rows
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_10029_Grantee";
DROP ROLE IF EXISTS dcl_10029_grantor;
DROP ROLE IF EXISTS dcl_10029_member;
CREATE ROLE "dcl_10029_Grantee";
CREATE ROLE dcl_10029_grantor;
CREATE ROLE dcl_10029_member;
DROP FUNCTION IF EXISTS dcl_10029_function(integer);
CREATE FUNCTION dcl_10029_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
GRANT EXECUTE ON FUNCTION dcl_10029_missing_object(integer) TO CURRENT_ROLE;
SET ROLE "dcl_10029_Grantee";
REVOKE ADMIN OPTION FOR EXECUTE ON FUNCTION dcl_10029_missing_object(integer) FROM CURRENT_ROLE GRANTED BY dcl_10029_grantor RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'table_privilege' AS privilege_scope;
DROP FUNCTION IF EXISTS dcl_10029_function(integer);
DROP OWNED BY "dcl_10029_Grantee";
DROP OWNED BY dcl_10029_member;
DROP OWNED BY dcl_10029_grantor;
DROP ROLE IF EXISTS dcl_10029_member;
DROP ROLE IF EXISTS dcl_10029_grantor;
DROP ROLE IF EXISTS "dcl_10029_Grantee";
