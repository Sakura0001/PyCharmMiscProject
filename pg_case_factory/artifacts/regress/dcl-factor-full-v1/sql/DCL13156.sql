-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_15 (role_membership) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_15
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=role_name
-- factor grant_option_shape=grant_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=missing_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=effect_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_13156_grantor;
DROP ROLE IF EXISTS dcl_13156_member;
CREATE ROLE dcl_13156_grantor;
CREATE ROLE dcl_13156_member;
GRANT dcl_13156_missing_member TO dcl_13156_grantor WITH GRANT OPTION;
GRANT dcl_13156_grantor TO dcl_13156_member WITH SET TRUE;
SET ROLE dcl_13156_member;
SET ROLE dcl_13156_grantor;
REVOKE GRANT OPTION FOR dcl_13156_missing_member FROM dcl_13156_missing_role RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_13156_member;
DROP OWNED BY dcl_13156_grantor;
DROP ROLE IF EXISTS dcl_13156_member;
DROP ROLE IF EXISTS dcl_13156_grantor;
