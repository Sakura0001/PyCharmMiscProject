-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_12 (schema) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_12
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
-- factor grantee_shape=session_user
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
DROP ROLE IF EXISTS dcl_12206_grantee;
DROP ROLE IF EXISTS dcl_12206_grantor;
DROP ROLE IF EXISTS dcl_12206_member;
CREATE ROLE dcl_12206_grantee;
CREATE ROLE dcl_12206_grantor;
CREATE ROLE dcl_12206_member;
DROP SCHEMA IF EXISTS dcl_12206_schema CASCADE;
CREATE SCHEMA dcl_12206_schema;
GRANT USAGE ON SCHEMA dcl_12206_missing_object TO SESSION_USER;
BEGIN;
SET ROLE dcl_12206_grantee;
REVOKE USAGE ON SCHEMA dcl_12206_missing_object FROM SESSION_USER GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
ROLLBACK;
DROP SCHEMA IF EXISTS dcl_12206_schema CASCADE;
DROP OWNED BY dcl_12206_grantee;
DROP OWNED BY dcl_12206_member;
DROP OWNED BY dcl_12206_grantor;
DROP ROLE IF EXISTS dcl_12206_member;
DROP ROLE IF EXISTS dcl_12206_grantor;
DROP ROLE IF EXISTS dcl_12206_grantee;
