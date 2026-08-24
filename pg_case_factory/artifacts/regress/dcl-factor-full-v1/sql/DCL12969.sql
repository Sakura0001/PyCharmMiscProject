-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_14 (type) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
-- factor expected_status=failure
-- factor privilege_scope=role_membership
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
DROP ROLE IF EXISTS "dcl_12969_Grantee";
DROP ROLE IF EXISTS dcl_12969_grantor;
DROP ROLE IF EXISTS dcl_12969_member;
CREATE ROLE "dcl_12969_Grantee";
CREATE ROLE dcl_12969_grantor;
CREATE ROLE dcl_12969_member;
DROP TYPE IF EXISTS dcl_12969_type;
CREATE TYPE dcl_12969_type AS ENUM ('alpha', 'beta');
GRANT USAGE ON TYPE dcl_12969_missing_object TO CURRENT_ROLE;
SET ROLE "dcl_12969_Grantee";
REVOKE ADMIN OPTION FOR USAGE ON TYPE dcl_12969_missing_object FROM CURRENT_ROLE GRANTED BY dcl_12969_grantor RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'role_membership' AS privilege_scope;
DROP TYPE IF EXISTS dcl_12969_type;
DROP OWNED BY "dcl_12969_Grantee";
DROP OWNED BY dcl_12969_member;
DROP OWNED BY dcl_12969_grantor;
DROP ROLE IF EXISTS dcl_12969_member;
DROP ROLE IF EXISTS dcl_12969_grantor;
DROP ROLE IF EXISTS "dcl_12969_Grantee";
