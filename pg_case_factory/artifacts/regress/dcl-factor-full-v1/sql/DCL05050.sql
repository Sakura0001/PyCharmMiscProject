-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_12 (schema) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_12
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=current_user
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
DROP ROLE IF EXISTS dcl_05050_grantor;
DROP ROLE IF EXISTS dcl_05050_member;
CREATE ROLE dcl_05050_grantor;
CREATE ROLE dcl_05050_member;
DROP SCHEMA IF EXISTS dcl_05050_schema CASCADE;
CREATE SCHEMA dcl_05050_schema;
GRANT USAGE ON SCHEMA dcl_05050_missing_object TO dcl_05050_grantor WITH GRANT OPTION;
GRANT dcl_05050_grantor TO dcl_05050_member WITH SET TRUE;
SET ROLE dcl_05050_member;
SET ROLE dcl_05050_grantor;
GRANT USAGE ON SCHEMA dcl_05050_missing_object TO CURRENT_USER WITH GRANT OPTION;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
RESET ROLE;
RESET ALL;
DROP SCHEMA IF EXISTS dcl_05050_schema CASCADE;
DROP OWNED BY dcl_05050_member;
DROP OWNED BY dcl_05050_grantor;
DROP ROLE IF EXISTS dcl_05050_member;
DROP ROLE IF EXISTS dcl_05050_grantor;
