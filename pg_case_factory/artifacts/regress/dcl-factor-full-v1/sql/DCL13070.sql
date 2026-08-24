-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_14 (type) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
-- factor grantee_shape=public
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
DROP ROLE IF EXISTS dcl_13070_grantee;
DROP ROLE IF EXISTS dcl_13070_grantor;
DROP ROLE IF EXISTS dcl_13070_member;
CREATE ROLE dcl_13070_grantee;
CREATE ROLE dcl_13070_grantor;
CREATE ROLE dcl_13070_member;
DROP TYPE IF EXISTS dcl_13070_type;
CREATE TYPE dcl_13070_type AS ENUM ('alpha', 'beta');
GRANT USAGE ON TYPE dcl_13070_missing_object TO PUBLIC;
BEGIN;
SET ROLE dcl_13070_grantee;
REVOKE USAGE ON TYPE dcl_13070_missing_object FROM PUBLIC GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
ROLLBACK;
DROP TYPE IF EXISTS dcl_13070_type;
DROP OWNED BY dcl_13070_grantee;
DROP OWNED BY dcl_13070_member;
DROP OWNED BY dcl_13070_grantor;
DROP ROLE IF EXISTS dcl_13070_member;
DROP ROLE IF EXISTS dcl_13070_grantor;
DROP ROLE IF EXISTS dcl_13070_grantee;
