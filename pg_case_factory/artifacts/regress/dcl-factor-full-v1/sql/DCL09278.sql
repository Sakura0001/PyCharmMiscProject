-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_6 (foreign_data_wrapper) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_6
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
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
DROP ROLE IF EXISTS dcl_09278_grantee;
DROP ROLE IF EXISTS dcl_09278_grantor;
DROP ROLE IF EXISTS dcl_09278_member;
CREATE ROLE dcl_09278_grantee;
CREATE ROLE dcl_09278_grantor;
CREATE ROLE dcl_09278_member;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09278_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_09278_fdw;
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_09278_missing_object TO dcl_09278_grantee;
BEGIN;
SET ROLE dcl_09278_grantee;
REVOKE USAGE ON FOREIGN DATA WRAPPER dcl_09278_missing_object FROM dcl_09278_grantee GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
ROLLBACK;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09278_fdw CASCADE;
DROP OWNED BY dcl_09278_grantee;
DROP OWNED BY dcl_09278_member;
DROP OWNED BY dcl_09278_grantor;
DROP ROLE IF EXISTS dcl_09278_member;
DROP ROLE IF EXISTS dcl_09278_grantor;
DROP ROLE IF EXISTS dcl_09278_grantee;
