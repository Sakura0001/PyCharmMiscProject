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
-- factor expected_status=success
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=current_role
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=none
-- factor ownership_boundary=owner
-- factor verification_mode=returned_rows
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS dcl_09084_grantee;
DROP ROLE IF EXISTS dcl_09084_grantor;
DROP ROLE IF EXISTS dcl_09084_member;
CREATE ROLE dcl_09084_grantee;
CREATE ROLE dcl_09084_grantor;
CREATE ROLE dcl_09084_member;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09084_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_09084_fdw;
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_09084_fdw TO CURRENT_ROLE;
REVOKE GRANT OPTION FOR USAGE ON FOREIGN DATA WRAPPER dcl_09084_fdw FROM CURRENT_ROLE GRANTED BY dcl_09084_grantor RESTRICT;
SELECT 'revoke' AS completed_statement, 'routine_language_type_fdw_server' AS privilege_scope;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09084_fdw CASCADE;
DROP OWNED BY dcl_09084_grantee;
DROP OWNED BY dcl_09084_member;
DROP OWNED BY dcl_09084_grantor;
DROP ROLE IF EXISTS dcl_09084_member;
DROP ROLE IF EXISTS dcl_09084_grantor;
DROP ROLE IF EXISTS dcl_09084_grantee;
