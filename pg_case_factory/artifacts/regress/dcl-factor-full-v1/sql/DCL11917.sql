-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_12 (schema) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_12
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
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
DROP ROLE IF EXISTS dcl_11917_grantor;
DROP ROLE IF EXISTS dcl_11917_member;
CREATE ROLE dcl_11917_grantor;
CREATE ROLE dcl_11917_member;
DROP SCHEMA IF EXISTS dcl_11917_schema CASCADE;
CREATE SCHEMA dcl_11917_schema;
GRANT USAGE ON SCHEMA dcl_11917_missing_object TO dcl_11917_missing_role;
GRANT USAGE ON SCHEMA dcl_11917_missing_object TO dcl_11917_grantor WITH GRANT OPTION;
GRANT dcl_11917_grantor TO dcl_11917_member WITH SET TRUE;
SET ROLE dcl_11917_member;
SET ROLE dcl_11917_grantor;
REVOKE USAGE ON SCHEMA dcl_11917_missing_object FROM dcl_11917_missing_role RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'schema_database_tablespace' AS privilege_scope;
RESET ROLE;
RESET ALL;
DROP SCHEMA IF EXISTS dcl_11917_schema CASCADE;
DROP OWNED BY dcl_11917_member;
DROP OWNED BY dcl_11917_grantor;
DROP ROLE IF EXISTS dcl_11917_member;
DROP ROLE IF EXISTS dcl_11917_grantor;
