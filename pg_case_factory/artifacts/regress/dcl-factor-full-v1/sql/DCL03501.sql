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
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=returned_rows
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_03501_Grantee";
DROP ROLE IF EXISTS dcl_03501_grantor;
DROP ROLE IF EXISTS dcl_03501_member;
CREATE ROLE "dcl_03501_Grantee";
CREATE ROLE dcl_03501_grantor;
CREATE ROLE dcl_03501_member;
DROP FUNCTION IF EXISTS dcl_03501_function(integer);
CREATE FUNCTION dcl_03501_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
SET ROLE "dcl_03501_Grantee";
GRANT EXECUTE ON FUNCTION dcl_03501_missing_object(integer) TO SESSION_USER GRANTED BY dcl_03501_grantor;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'role_membership' AS privilege_scope;
DROP FUNCTION IF EXISTS dcl_03501_function(integer);
DROP OWNED BY "dcl_03501_Grantee";
DROP OWNED BY dcl_03501_member;
DROP OWNED BY dcl_03501_grantor;
DROP ROLE IF EXISTS dcl_03501_member;
DROP ROLE IF EXISTS dcl_03501_grantor;
DROP ROLE IF EXISTS "dcl_03501_Grantee";
