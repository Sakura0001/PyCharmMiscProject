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
-- factor grantee_shape=session_user
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
DROP ROLE IF EXISTS dcl_12025_grantor;
DROP ROLE IF EXISTS dcl_12025_member;
CREATE ROLE dcl_12025_grantor;
CREATE ROLE dcl_12025_member;
DROP SCHEMA IF EXISTS dcl_12025_schema CASCADE;
CREATE SCHEMA dcl_12025_schema;
GRANT USAGE ON SCHEMA dcl_12025_missing_object TO SESSION_USER;
GRANT USAGE ON SCHEMA dcl_12025_missing_object TO dcl_12025_grantor WITH GRANT OPTION;
GRANT dcl_12025_grantor TO dcl_12025_member WITH SET TRUE;
SET ROLE dcl_12025_member;
SET ROLE dcl_12025_grantor;
REVOKE USAGE ON SCHEMA dcl_12025_missing_object FROM SESSION_USER RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'routine_language_type_fdw_server' AS privilege_scope;
RESET ROLE;
RESET ALL;
DROP SCHEMA IF EXISTS dcl_12025_schema CASCADE;
DROP OWNED BY dcl_12025_member;
DROP OWNED BY dcl_12025_grantor;
DROP ROLE IF EXISTS dcl_12025_member;
DROP ROLE IF EXISTS dcl_12025_grantor;
