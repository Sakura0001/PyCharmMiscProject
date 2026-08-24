-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_15 (role_membership) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_15
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=public
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_13475_grantee;
DROP ROLE IF EXISTS dcl_13475_grantor;
DROP ROLE IF EXISTS dcl_13475_member;
CREATE ROLE dcl_13475_grantee;
CREATE ROLE dcl_13475_grantor;
CREATE ROLE dcl_13475_member;
BEGIN;
SET ROLE dcl_13475_grantee;
REVOKE SET OPTION FOR dcl_13475_missing_member FROM PUBLIC GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT true AS role_membership_statement_completed;
ROLLBACK;
DROP OWNED BY dcl_13475_grantee;
DROP OWNED BY dcl_13475_member;
DROP OWNED BY dcl_13475_grantor;
DROP ROLE IF EXISTS dcl_13475_member;
DROP ROLE IF EXISTS dcl_13475_grantor;
DROP ROLE IF EXISTS dcl_13475_grantee;
