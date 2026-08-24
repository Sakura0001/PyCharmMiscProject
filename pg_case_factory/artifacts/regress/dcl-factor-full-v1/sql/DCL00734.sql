-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_2 (column) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=current_user
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
DROP TABLE IF EXISTS dcl_00734_schema.dcl_00734_table;
DROP ROLE IF EXISTS dcl_00734_grantee;
DROP ROLE IF EXISTS dcl_00734_grantor;
DROP ROLE IF EXISTS dcl_00734_member;
CREATE ROLE dcl_00734_grantee;
CREATE ROLE dcl_00734_grantor;
CREATE ROLE dcl_00734_member;
DROP SCHEMA IF EXISTS dcl_00734_schema CASCADE;
CREATE SCHEMA dcl_00734_schema;
CREATE TABLE dcl_00734_schema.dcl_00734_table (id integer, payload text);
BEGIN;
SET ROLE dcl_00734_grantee;
GRANT EXECUTE (payload) ON TABLE dcl_00734_missing_object.dcl_00734_table TO CURRENT_USER WITH ADMIN OPTION GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
ROLLBACK;
DROP SCHEMA IF EXISTS dcl_00734_schema CASCADE;
DROP OWNED BY dcl_00734_grantee;
DROP OWNED BY dcl_00734_member;
DROP OWNED BY dcl_00734_grantor;
DROP ROLE IF EXISTS dcl_00734_member;
DROP ROLE IF EXISTS dcl_00734_grantor;
DROP ROLE IF EXISTS dcl_00734_grantee;
DROP TABLE IF EXISTS dcl_00734_schema.dcl_00734_table;
