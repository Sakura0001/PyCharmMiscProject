-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_4 (database) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_4
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=role_name
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=plain_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=error_assertion
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_08438_grantee;
DROP ROLE IF EXISTS dcl_08438_grantor;
DROP ROLE IF EXISTS dcl_08438_member;
CREATE ROLE dcl_08438_grantee;
CREATE ROLE dcl_08438_grantor;
CREATE ROLE dcl_08438_member;
GRANT CONNECT ON DATABASE dcl_08438_missing_object TO dcl_08438_grantee;
BEGIN;
SET ROLE dcl_08438_grantee;
REVOKE CONNECT ON DATABASE dcl_08438_missing_object FROM dcl_08438_grantee GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
ROLLBACK;
DROP OWNED BY dcl_08438_grantee;
DROP OWNED BY dcl_08438_member;
DROP OWNED BY dcl_08438_grantor;
DROP ROLE IF EXISTS dcl_08438_member;
DROP ROLE IF EXISTS dcl_08438_grantor;
DROP ROLE IF EXISTS dcl_08438_grantee;
