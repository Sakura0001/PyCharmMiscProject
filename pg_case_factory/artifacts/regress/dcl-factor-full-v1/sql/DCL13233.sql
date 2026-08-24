-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_15 (role_membership) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_15
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
-- factor grantee_shape=public
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
DROP ROLE IF EXISTS "dcl_13233_Grantee";
DROP ROLE IF EXISTS dcl_13233_grantor;
DROP ROLE IF EXISTS dcl_13233_member;
CREATE ROLE "dcl_13233_Grantee";
CREATE ROLE dcl_13233_grantor;
CREATE ROLE dcl_13233_member;
SET ROLE "dcl_13233_Grantee";
REVOKE ADMIN OPTION FOR dcl_13233_missing_member FROM PUBLIC GRANTED BY dcl_13233_grantor RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'column_privilege' AS privilege_scope;
DROP OWNED BY "dcl_13233_Grantee";
DROP OWNED BY dcl_13233_member;
DROP OWNED BY dcl_13233_grantor;
DROP ROLE IF EXISTS dcl_13233_member;
DROP ROLE IF EXISTS dcl_13233_grantor;
DROP ROLE IF EXISTS "dcl_13233_Grantee";
