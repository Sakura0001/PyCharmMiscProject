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
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=missing_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=returned_rows
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_09277_grantor;
DROP ROLE IF EXISTS dcl_09277_member;
CREATE ROLE dcl_09277_grantor;
CREATE ROLE dcl_09277_member;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09277_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_09277_fdw;
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_09277_missing_object TO dcl_09277_missing_role;
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_09277_missing_object TO dcl_09277_grantor WITH GRANT OPTION;
GRANT dcl_09277_grantor TO dcl_09277_member WITH SET TRUE;
SET ROLE dcl_09277_member;
SET ROLE dcl_09277_grantor;
REVOKE USAGE ON FOREIGN DATA WRAPPER dcl_09277_missing_object FROM dcl_09277_missing_role RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'routine_language_type_fdw_server' AS privilege_scope;
RESET ROLE;
RESET ALL;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09277_fdw CASCADE;
DROP OWNED BY dcl_09277_member;
DROP OWNED BY dcl_09277_grantor;
DROP ROLE IF EXISTS dcl_09277_member;
DROP ROLE IF EXISTS dcl_09277_grantor;
