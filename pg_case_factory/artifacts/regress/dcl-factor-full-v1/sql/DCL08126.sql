-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_3 (sequence) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_3
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
-- factor grantee_shape=public
-- factor grant_option_shape=admin_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=plain_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=error_assertion
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_08126_grantee;
DROP ROLE IF EXISTS dcl_08126_grantor;
DROP ROLE IF EXISTS dcl_08126_member;
CREATE ROLE dcl_08126_grantee;
CREATE ROLE dcl_08126_grantor;
CREATE ROLE dcl_08126_member;
DROP SEQUENCE IF EXISTS dcl_08126_sequence;
CREATE SEQUENCE dcl_08126_sequence;
GRANT USAGE ON SEQUENCE dcl_08126_missing_object TO PUBLIC;
BEGIN;
SET ROLE dcl_08126_grantee;
REVOKE ADMIN OPTION FOR USAGE ON SEQUENCE dcl_08126_missing_object FROM PUBLIC GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
ROLLBACK;
DROP SEQUENCE IF EXISTS dcl_08126_sequence;
DROP OWNED BY dcl_08126_grantee;
DROP OWNED BY dcl_08126_member;
DROP OWNED BY dcl_08126_grantor;
DROP ROLE IF EXISTS dcl_08126_member;
DROP ROLE IF EXISTS dcl_08126_grantor;
DROP ROLE IF EXISTS dcl_08126_grantee;
