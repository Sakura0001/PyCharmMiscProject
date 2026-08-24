-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_12 (schema) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_12
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=current_user
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=quoted_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=error_assertion
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_12138_Grantee";
DROP ROLE IF EXISTS dcl_12138_grantor;
DROP ROLE IF EXISTS dcl_12138_member;
CREATE ROLE "dcl_12138_Grantee";
CREATE ROLE dcl_12138_grantor;
CREATE ROLE dcl_12138_member;
DROP SCHEMA IF EXISTS dcl_12138_schema CASCADE;
CREATE SCHEMA dcl_12138_schema;
GRANT USAGE ON SCHEMA dcl_12138_missing_object TO CURRENT_USER;
SET ROLE "dcl_12138_Grantee";
REVOKE GRANT OPTION FOR USAGE ON SCHEMA dcl_12138_missing_object FROM CURRENT_USER GRANTED BY dcl_12138_grantor RESTRICT;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
DROP SCHEMA IF EXISTS dcl_12138_schema CASCADE;
DROP OWNED BY "dcl_12138_Grantee";
DROP OWNED BY dcl_12138_member;
DROP OWNED BY dcl_12138_grantor;
DROP ROLE IF EXISTS dcl_12138_member;
DROP ROLE IF EXISTS dcl_12138_grantor;
DROP ROLE IF EXISTS "dcl_12138_Grantee";
