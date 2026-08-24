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
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=current_role
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=missing_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=effect_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_06640_grantor;
DROP ROLE IF EXISTS dcl_06640_member;
CREATE ROLE dcl_06640_grantor;
CREATE ROLE dcl_06640_member;
GRANT dcl_06640_missing_member TO dcl_06640_grantor WITH GRANT OPTION;
GRANT dcl_06640_grantor TO dcl_06640_member WITH SET TRUE;
SET ROLE dcl_06640_member;
SET ROLE dcl_06640_grantor;
GRANT dcl_06640_missing_member TO CURRENT_ROLE WITH INHERIT TRUE;
RESET ROLE;
SELECT true AS privilege_effect_observed;
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_06640_member;
DROP OWNED BY dcl_06640_grantor;
DROP ROLE IF EXISTS dcl_06640_member;
DROP ROLE IF EXISTS dcl_06640_grantor;
