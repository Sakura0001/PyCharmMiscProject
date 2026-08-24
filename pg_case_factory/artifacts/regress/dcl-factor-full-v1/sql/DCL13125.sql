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
-- factor grantee_shape=role_name
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=member_role
-- factor verification_mode=returned_rows
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_13125_Grantee";
DROP ROLE IF EXISTS dcl_13125_grantor;
DROP ROLE IF EXISTS dcl_13125_member;
CREATE ROLE "dcl_13125_Grantee";
CREATE ROLE dcl_13125_grantor;
CREATE ROLE dcl_13125_member;
GRANT dcl_13125_member TO dcl_13125_grantor WITH GRANT OPTION;
SET ROLE dcl_13125_grantor;
REVOKE SET OPTION FOR dcl_13125_member FROM "dcl_13125_Grantee" GRANTED BY dcl_13125_grantor RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'role_membership' AS privilege_scope;
DROP OWNED BY "dcl_13125_Grantee";
DROP OWNED BY dcl_13125_member;
DROP OWNED BY dcl_13125_grantor;
DROP ROLE IF EXISTS dcl_13125_member;
DROP ROLE IF EXISTS dcl_13125_grantor;
DROP ROLE IF EXISTS "dcl_13125_Grantee";
