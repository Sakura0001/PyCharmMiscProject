-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_1 (table) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=current_role
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
DROP TABLE IF EXISTS dcl_07118_schema.dcl_07118_table;
DROP ROLE IF EXISTS dcl_07118_grantee;
DROP ROLE IF EXISTS dcl_07118_grantor;
DROP ROLE IF EXISTS dcl_07118_member;
CREATE ROLE dcl_07118_grantee;
CREATE ROLE dcl_07118_grantor;
CREATE ROLE dcl_07118_member;
DROP SCHEMA IF EXISTS dcl_07118_schema CASCADE;
CREATE SCHEMA dcl_07118_schema;
CREATE TABLE dcl_07118_schema.dcl_07118_table (id integer, payload text);
GRANT SELECT ON TABLE dcl_07118_missing_object.dcl_07118_table TO CURRENT_ROLE;
BEGIN;
SET ROLE dcl_07118_grantee;
REVOKE ADMIN OPTION FOR SELECT ON TABLE dcl_07118_missing_object.dcl_07118_table FROM CURRENT_ROLE GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
ROLLBACK;
DROP SCHEMA IF EXISTS dcl_07118_schema CASCADE;
DROP OWNED BY dcl_07118_grantee;
DROP OWNED BY dcl_07118_member;
DROP OWNED BY dcl_07118_grantor;
DROP ROLE IF EXISTS dcl_07118_member;
DROP ROLE IF EXISTS dcl_07118_grantor;
DROP ROLE IF EXISTS dcl_07118_grantee;
DROP TABLE IF EXISTS dcl_07118_schema.dcl_07118_table;
