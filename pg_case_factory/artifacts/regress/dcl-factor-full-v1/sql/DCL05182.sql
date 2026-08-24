-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_12 (schema) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_12
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=session_user
-- factor grant_option_shape=grant_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=missing_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=error_assertion
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_05182_grantor;
DROP ROLE IF EXISTS dcl_05182_member;
CREATE ROLE dcl_05182_grantor;
CREATE ROLE dcl_05182_member;
DROP SCHEMA IF EXISTS dcl_05182_schema CASCADE;
CREATE SCHEMA dcl_05182_schema;
GRANT USAGE ON SCHEMA dcl_05182_missing_object TO dcl_05182_grantor WITH GRANT OPTION;
GRANT dcl_05182_grantor TO dcl_05182_member WITH SET TRUE;
SET ROLE dcl_05182_member;
SET ROLE dcl_05182_grantor;
GRANT USAGE ON SCHEMA dcl_05182_missing_object TO SESSION_USER WITH GRANT OPTION;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
RESET ROLE;
RESET ALL;
DROP SCHEMA IF EXISTS dcl_05182_schema CASCADE;
DROP OWNED BY dcl_05182_member;
DROP OWNED BY dcl_05182_grantor;
DROP ROLE IF EXISTS dcl_05182_member;
DROP ROLE IF EXISTS dcl_05182_grantor;
