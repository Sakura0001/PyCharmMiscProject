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
-- factor expected_status=success
-- factor privilege_scope=role_membership
-- factor grantee_shape=current_user
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=member_role
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS "dcl_13141_Grantee";
DROP ROLE IF EXISTS dcl_13141_grantor;
DROP ROLE IF EXISTS dcl_13141_member;
CREATE ROLE "dcl_13141_Grantee";
CREATE ROLE dcl_13141_grantor;
CREATE ROLE dcl_13141_member;
GRANT dcl_13141_member TO dcl_13141_grantor WITH GRANT OPTION;
SET ROLE dcl_13141_grantor;
REVOKE SET OPTION FOR dcl_13141_member FROM CURRENT_USER RESTRICT;
RESET ROLE;
SELECT true AS role_membership_statement_completed;
RESET ROLE;
RESET ALL;
DROP OWNED BY "dcl_13141_Grantee";
DROP OWNED BY dcl_13141_member;
DROP OWNED BY dcl_13141_grantor;
DROP ROLE IF EXISTS dcl_13141_member;
DROP ROLE IF EXISTS dcl_13141_grantor;
DROP ROLE IF EXISTS "dcl_13141_Grantee";
