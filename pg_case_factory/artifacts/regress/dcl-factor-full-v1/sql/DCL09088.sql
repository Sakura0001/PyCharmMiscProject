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
-- factor grantee_shape=current_user
-- factor grant_option_shape=grant_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=none
-- factor ownership_boundary=owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_09088_grantee;
DROP ROLE IF EXISTS dcl_09088_grantor;
DROP ROLE IF EXISTS dcl_09088_member;
CREATE ROLE dcl_09088_grantee;
CREATE ROLE dcl_09088_grantor;
CREATE ROLE dcl_09088_member;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09088_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_09088_fdw;
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_09088_fdw TO CURRENT_USER;
REVOKE GRANT OPTION FOR USAGE ON FOREIGN DATA WRAPPER dcl_09088_fdw FROM CURRENT_USER RESTRICT;
SELECT true AS fdw_privilege_statement_completed;
RESET ROLE;
RESET ALL;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09088_fdw CASCADE;
DROP OWNED BY dcl_09088_grantee;
DROP OWNED BY dcl_09088_member;
DROP OWNED BY dcl_09088_grantor;
DROP ROLE IF EXISTS dcl_09088_member;
DROP ROLE IF EXISTS dcl_09088_grantor;
DROP ROLE IF EXISTS dcl_09088_grantee;
