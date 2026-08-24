-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_7 (foreign_server) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_7
-- factor expected_status=failure
-- factor privilege_scope=role_membership
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
DROP ROLE IF EXISTS "dcl_03006_Grantee";
DROP ROLE IF EXISTS dcl_03006_grantor;
DROP ROLE IF EXISTS dcl_03006_member;
CREATE ROLE "dcl_03006_Grantee";
CREATE ROLE dcl_03006_grantor;
CREATE ROLE dcl_03006_member;
DROP SERVER IF EXISTS dcl_03006_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_03006_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_03006_fdw;
CREATE SERVER dcl_03006_server FOREIGN DATA WRAPPER dcl_03006_fdw;
SET ROLE "dcl_03006_Grantee";
GRANT USAGE ON FOREIGN SERVER dcl_03006_missing_object TO "dcl_03006_Grantee" WITH GRANT OPTION GRANTED BY dcl_03006_grantor;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
DROP SERVER IF EXISTS dcl_03006_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_03006_fdw CASCADE;
DROP OWNED BY "dcl_03006_Grantee";
DROP OWNED BY dcl_03006_member;
DROP OWNED BY dcl_03006_grantor;
DROP ROLE IF EXISTS dcl_03006_member;
DROP ROLE IF EXISTS dcl_03006_grantor;
DROP ROLE IF EXISTS "dcl_03006_Grantee";
