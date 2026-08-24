-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_1 (table) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=role_name
-- factor grant_option_shape=admin_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=plain_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=error_assertion
-- factor cleanup_mode=rollback
DROP TABLE IF EXISTS dcl_06974_schema.dcl_06974_table;
DROP ROLE IF EXISTS dcl_06974_grantee;
DROP ROLE IF EXISTS dcl_06974_grantor;
DROP ROLE IF EXISTS dcl_06974_member;
CREATE ROLE dcl_06974_grantee;
CREATE ROLE dcl_06974_grantor;
CREATE ROLE dcl_06974_member;
DROP SCHEMA IF EXISTS dcl_06974_schema CASCADE;
CREATE SCHEMA dcl_06974_schema;
CREATE TABLE dcl_06974_schema.dcl_06974_table (id integer, payload text);
GRANT SELECT ON TABLE dcl_06974_missing_object.dcl_06974_table TO dcl_06974_grantee;
BEGIN;
SET ROLE dcl_06974_grantee;
REVOKE ADMIN OPTION FOR SELECT ON TABLE dcl_06974_missing_object.dcl_06974_table FROM dcl_06974_grantee GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
ROLLBACK;
DROP SCHEMA IF EXISTS dcl_06974_schema CASCADE;
DROP OWNED BY dcl_06974_grantee;
DROP OWNED BY dcl_06974_member;
DROP OWNED BY dcl_06974_grantor;
DROP ROLE IF EXISTS dcl_06974_member;
DROP ROLE IF EXISTS dcl_06974_grantor;
DROP ROLE IF EXISTS dcl_06974_grantee;
DROP TABLE IF EXISTS dcl_06974_schema.dcl_06974_table;
