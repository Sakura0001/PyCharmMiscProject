-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_15 (role_membership) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_15
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=session_user
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=plain_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=effect_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_06716_grantee;
DROP ROLE IF EXISTS dcl_06716_grantor;
DROP ROLE IF EXISTS dcl_06716_member;
CREATE ROLE dcl_06716_grantee;
CREATE ROLE dcl_06716_grantor;
CREATE ROLE dcl_06716_member;
BEGIN;
SET ROLE dcl_06716_grantee;
GRANT dcl_06716_missing_member TO SESSION_USER GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP OWNED BY dcl_06716_grantee;
DROP OWNED BY dcl_06716_member;
DROP OWNED BY dcl_06716_grantor;
DROP ROLE IF EXISTS dcl_06716_member;
DROP ROLE IF EXISTS dcl_06716_grantor;
DROP ROLE IF EXISTS dcl_06716_grantee;
