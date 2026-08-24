-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_1 (table) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
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
DROP TABLE IF EXISTS dcl_07250_schema.dcl_07250_table;
DROP ROLE IF EXISTS dcl_07250_grantee;
DROP ROLE IF EXISTS dcl_07250_grantor;
DROP ROLE IF EXISTS dcl_07250_member;
CREATE ROLE dcl_07250_grantee;
CREATE ROLE dcl_07250_grantor;
CREATE ROLE dcl_07250_member;
DROP SCHEMA IF EXISTS dcl_07250_schema CASCADE;
CREATE SCHEMA dcl_07250_schema;
CREATE TABLE dcl_07250_schema.dcl_07250_table (id integer, payload text);
GRANT MAINTAIN ON TABLE dcl_07250_missing_object.dcl_07250_table TO CURRENT_USER;
BEGIN;
SET ROLE dcl_07250_grantee;
REVOKE ADMIN OPTION FOR MAINTAIN ON TABLE dcl_07250_missing_object.dcl_07250_table FROM CURRENT_USER GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
ROLLBACK;
DROP SCHEMA IF EXISTS dcl_07250_schema CASCADE;
DROP OWNED BY dcl_07250_grantee;
DROP OWNED BY dcl_07250_member;
DROP OWNED BY dcl_07250_grantor;
DROP ROLE IF EXISTS dcl_07250_member;
DROP ROLE IF EXISTS dcl_07250_grantor;
DROP ROLE IF EXISTS dcl_07250_grantee;
DROP TABLE IF EXISTS dcl_07250_schema.dcl_07250_table;
