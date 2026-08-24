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
-- factor grantee_shape=session_user
-- factor grant_option_shape=admin_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=plain_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=effect_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_13268_grantee;
DROP ROLE IF EXISTS dcl_13268_grantor;
DROP ROLE IF EXISTS dcl_13268_member;
CREATE ROLE dcl_13268_grantee;
CREATE ROLE dcl_13268_grantor;
CREATE ROLE dcl_13268_member;
BEGIN;
SET ROLE dcl_13268_grantee;
REVOKE ADMIN OPTION FOR dcl_13268_missing_member FROM SESSION_USER GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP OWNED BY dcl_13268_grantee;
DROP OWNED BY dcl_13268_member;
DROP OWNED BY dcl_13268_grantor;
DROP ROLE IF EXISTS dcl_13268_member;
DROP ROLE IF EXISTS dcl_13268_grantor;
DROP ROLE IF EXISTS dcl_13268_grantee;
