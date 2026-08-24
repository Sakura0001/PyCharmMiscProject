-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_6 (foreign_data_wrapper) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_6
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=role_name
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
DROP ROLE IF EXISTS "dcl_09402_Grantee";
DROP ROLE IF EXISTS dcl_09402_grantor;
DROP ROLE IF EXISTS dcl_09402_member;
CREATE ROLE "dcl_09402_Grantee";
CREATE ROLE dcl_09402_grantor;
CREATE ROLE dcl_09402_member;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09402_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_09402_fdw;
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_09402_missing_object TO "dcl_09402_Grantee";
SET ROLE "dcl_09402_Grantee";
REVOKE GRANT OPTION FOR USAGE ON FOREIGN DATA WRAPPER dcl_09402_missing_object FROM "dcl_09402_Grantee" GRANTED BY dcl_09402_grantor RESTRICT;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09402_fdw CASCADE;
DROP OWNED BY "dcl_09402_Grantee";
DROP OWNED BY dcl_09402_member;
DROP OWNED BY dcl_09402_grantor;
DROP ROLE IF EXISTS dcl_09402_member;
DROP ROLE IF EXISTS dcl_09402_grantor;
DROP ROLE IF EXISTS "dcl_09402_Grantee";
