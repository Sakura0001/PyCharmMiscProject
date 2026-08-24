-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_15 (role_membership) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_15
-- factor expected_status=success
-- factor privilege_scope=role_membership
-- factor grantee_shape=current_role
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=none
-- factor ownership_boundary=owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_06340_grantee;
DROP ROLE IF EXISTS dcl_06340_grantor;
DROP ROLE IF EXISTS dcl_06340_member;
CREATE ROLE dcl_06340_grantee;
CREATE ROLE dcl_06340_grantor;
CREATE ROLE dcl_06340_member;
GRANT dcl_06340_member TO CURRENT_ROLE;
SELECT true AS role_membership_statement_completed;
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_06340_grantee;
DROP OWNED BY dcl_06340_member;
DROP OWNED BY dcl_06340_grantor;
DROP ROLE IF EXISTS dcl_06340_member;
DROP ROLE IF EXISTS dcl_06340_grantor;
DROP ROLE IF EXISTS dcl_06340_grantee;
