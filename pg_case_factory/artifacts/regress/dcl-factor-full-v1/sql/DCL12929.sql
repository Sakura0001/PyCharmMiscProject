-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_14 (type) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=session_user
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=returned_rows
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_12929_grantee;
DROP ROLE IF EXISTS dcl_12929_grantor;
DROP ROLE IF EXISTS dcl_12929_member;
CREATE ROLE dcl_12929_grantee;
CREATE ROLE dcl_12929_grantor;
CREATE ROLE dcl_12929_member;
DROP TYPE IF EXISTS dcl_12929_type;
CREATE TYPE dcl_12929_type AS ENUM ('alpha', 'beta');
GRANT USAGE ON TYPE dcl_12929_missing_object TO SESSION_USER;
BEGIN;
SET ROLE dcl_12929_grantee;
REVOKE GRANT OPTION FOR USAGE ON TYPE dcl_12929_missing_object FROM SESSION_USER GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'routine_language_type_fdw_server' AS privilege_scope;
ROLLBACK;
DROP TYPE IF EXISTS dcl_12929_type;
DROP OWNED BY dcl_12929_grantee;
DROP OWNED BY dcl_12929_member;
DROP OWNED BY dcl_12929_grantor;
DROP ROLE IF EXISTS dcl_12929_member;
DROP ROLE IF EXISTS dcl_12929_grantor;
DROP ROLE IF EXISTS dcl_12929_grantee;
