-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_12 (schema) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_12
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=public
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
DROP ROLE IF EXISTS "dcl_11994_Grantee";
DROP ROLE IF EXISTS dcl_11994_grantor;
DROP ROLE IF EXISTS dcl_11994_member;
CREATE ROLE "dcl_11994_Grantee";
CREATE ROLE dcl_11994_grantor;
CREATE ROLE dcl_11994_member;
DROP SCHEMA IF EXISTS dcl_11994_schema CASCADE;
CREATE SCHEMA dcl_11994_schema;
GRANT USAGE ON SCHEMA dcl_11994_missing_object TO PUBLIC;
SET ROLE "dcl_11994_Grantee";
REVOKE GRANT OPTION FOR USAGE ON SCHEMA dcl_11994_missing_object FROM PUBLIC GRANTED BY dcl_11994_grantor RESTRICT;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
DROP SCHEMA IF EXISTS dcl_11994_schema CASCADE;
DROP OWNED BY "dcl_11994_Grantee";
DROP OWNED BY dcl_11994_member;
DROP OWNED BY dcl_11994_grantor;
DROP ROLE IF EXISTS dcl_11994_member;
DROP ROLE IF EXISTS dcl_11994_grantor;
DROP ROLE IF EXISTS "dcl_11994_Grantee";
