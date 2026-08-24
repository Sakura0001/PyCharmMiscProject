-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_12 (schema) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_12
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=role_name
-- factor grant_option_shape=admin_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=missing_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=returned_rows
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_05137_grantor;
DROP ROLE IF EXISTS dcl_05137_member;
CREATE ROLE dcl_05137_grantor;
CREATE ROLE dcl_05137_member;
DROP SCHEMA IF EXISTS dcl_05137_schema CASCADE;
CREATE SCHEMA dcl_05137_schema;
GRANT USAGE ON SCHEMA dcl_05137_missing_object TO dcl_05137_grantor WITH GRANT OPTION;
GRANT dcl_05137_grantor TO dcl_05137_member WITH SET TRUE;
SET ROLE dcl_05137_member;
SET ROLE dcl_05137_grantor;
GRANT USAGE ON SCHEMA dcl_05137_missing_object TO dcl_05137_missing_role WITH ADMIN OPTION;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'schema_database_tablespace' AS privilege_scope;
RESET ROLE;
RESET ALL;
DROP SCHEMA IF EXISTS dcl_05137_schema CASCADE;
DROP OWNED BY dcl_05137_member;
DROP OWNED BY dcl_05137_grantor;
DROP ROLE IF EXISTS dcl_05137_member;
DROP ROLE IF EXISTS dcl_05137_grantor;
