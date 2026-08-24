-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_15 (role_membership) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_15
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=role_name
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
DROP ROLE IF EXISTS "dcl_13401_Grantee";
DROP ROLE IF EXISTS dcl_13401_grantor;
DROP ROLE IF EXISTS dcl_13401_member;
CREATE ROLE "dcl_13401_Grantee";
CREATE ROLE dcl_13401_grantor;
CREATE ROLE dcl_13401_member;
SET ROLE "dcl_13401_Grantee";
REVOKE ADMIN OPTION FOR dcl_13401_missing_member FROM "dcl_13401_Grantee" GRANTED BY dcl_13401_grantor RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'role_membership' AS privilege_scope;
DROP OWNED BY "dcl_13401_Grantee";
DROP OWNED BY dcl_13401_member;
DROP OWNED BY dcl_13401_grantor;
DROP ROLE IF EXISTS dcl_13401_member;
DROP ROLE IF EXISTS dcl_13401_grantor;
DROP ROLE IF EXISTS "dcl_13401_Grantee";
