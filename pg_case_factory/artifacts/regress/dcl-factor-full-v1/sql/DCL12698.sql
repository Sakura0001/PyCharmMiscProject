-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_14 (type) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
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
DROP ROLE IF EXISTS dcl_12698_grantee;
DROP ROLE IF EXISTS dcl_12698_grantor;
DROP ROLE IF EXISTS dcl_12698_member;
CREATE ROLE dcl_12698_grantee;
CREATE ROLE dcl_12698_grantor;
CREATE ROLE dcl_12698_member;
DROP TYPE IF EXISTS dcl_12698_type;
CREATE TYPE dcl_12698_type AS ENUM ('alpha', 'beta');
GRANT USAGE ON TYPE dcl_12698_missing_object TO dcl_12698_grantee;
BEGIN;
SET ROLE dcl_12698_grantee;
REVOKE USAGE ON TYPE dcl_12698_missing_object FROM dcl_12698_grantee GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
ROLLBACK;
DROP TYPE IF EXISTS dcl_12698_type;
DROP OWNED BY dcl_12698_grantee;
DROP OWNED BY dcl_12698_member;
DROP OWNED BY dcl_12698_grantor;
DROP ROLE IF EXISTS dcl_12698_member;
DROP ROLE IF EXISTS dcl_12698_grantor;
DROP ROLE IF EXISTS dcl_12698_grantee;
