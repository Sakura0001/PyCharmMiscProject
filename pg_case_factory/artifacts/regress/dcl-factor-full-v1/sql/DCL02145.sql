-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_5 (domain) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_5
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=current_user
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
DROP ROLE IF EXISTS "dcl_02145_Grantee";
DROP ROLE IF EXISTS dcl_02145_grantor;
DROP ROLE IF EXISTS dcl_02145_member;
CREATE ROLE "dcl_02145_Grantee";
CREATE ROLE dcl_02145_grantor;
CREATE ROLE dcl_02145_member;
DROP DOMAIN IF EXISTS dcl_02145_domain;
CREATE DOMAIN dcl_02145_domain AS text;
SET ROLE "dcl_02145_Grantee";
GRANT USAGE ON DOMAIN dcl_02145_missing_object TO CURRENT_USER WITH ADMIN OPTION GRANTED BY dcl_02145_grantor;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'role_membership' AS privilege_scope;
DROP DOMAIN IF EXISTS dcl_02145_domain;
DROP OWNED BY "dcl_02145_Grantee";
DROP OWNED BY dcl_02145_member;
DROP OWNED BY dcl_02145_grantor;
DROP ROLE IF EXISTS dcl_02145_member;
DROP ROLE IF EXISTS dcl_02145_grantor;
DROP ROLE IF EXISTS "dcl_02145_Grantee";
