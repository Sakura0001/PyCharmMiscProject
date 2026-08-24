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
-- factor grant_option_shape=admin_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=member_role
-- factor verification_mode=effect_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS "dcl_13139_Grantee";
DROP ROLE IF EXISTS dcl_13139_grantor;
DROP ROLE IF EXISTS dcl_13139_member;
CREATE ROLE "dcl_13139_Grantee";
CREATE ROLE dcl_13139_grantor;
CREATE ROLE dcl_13139_member;
GRANT dcl_13139_member TO dcl_13139_grantor WITH GRANT OPTION;
BEGIN;
SET ROLE dcl_13139_grantor;
REVOKE ADMIN OPTION FOR dcl_13139_member FROM CURRENT_USER GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP OWNED BY "dcl_13139_Grantee";
DROP OWNED BY dcl_13139_member;
DROP OWNED BY dcl_13139_grantor;
DROP ROLE IF EXISTS dcl_13139_member;
DROP ROLE IF EXISTS dcl_13139_grantor;
DROP ROLE IF EXISTS "dcl_13139_Grantee";
