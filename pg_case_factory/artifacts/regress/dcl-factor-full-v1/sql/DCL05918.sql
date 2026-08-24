-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_14 (type) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=role_name
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
DROP ROLE IF EXISTS dcl_05918_grantee;
DROP ROLE IF EXISTS dcl_05918_grantor;
DROP ROLE IF EXISTS dcl_05918_member;
CREATE ROLE dcl_05918_grantee;
CREATE ROLE dcl_05918_grantor;
CREATE ROLE dcl_05918_member;
DROP TYPE IF EXISTS dcl_05918_type;
CREATE TYPE dcl_05918_type AS ENUM ('alpha', 'beta');
BEGIN;
SET ROLE dcl_05918_grantee;
GRANT USAGE ON TYPE dcl_05918_missing_object TO dcl_05918_grantee WITH ADMIN OPTION GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
ROLLBACK;
DROP TYPE IF EXISTS dcl_05918_type;
DROP OWNED BY dcl_05918_grantee;
DROP OWNED BY dcl_05918_member;
DROP OWNED BY dcl_05918_grantor;
DROP ROLE IF EXISTS dcl_05918_member;
DROP ROLE IF EXISTS dcl_05918_grantor;
DROP ROLE IF EXISTS dcl_05918_grantee;
