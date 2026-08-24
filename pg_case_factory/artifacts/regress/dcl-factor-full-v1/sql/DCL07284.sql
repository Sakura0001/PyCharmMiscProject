-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_2 (column) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=success
-- factor privilege_scope=column_privilege
-- factor grantee_shape=current_role
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=none
-- factor ownership_boundary=owner
-- factor verification_mode=returned_rows
-- factor cleanup_mode=drop_objects
DROP TABLE IF EXISTS dcl_07284_schema.dcl_07284_table;
DROP ROLE IF EXISTS dcl_07284_grantee;
DROP ROLE IF EXISTS dcl_07284_grantor;
DROP ROLE IF EXISTS dcl_07284_member;
CREATE ROLE dcl_07284_grantee;
CREATE ROLE dcl_07284_grantor;
CREATE ROLE dcl_07284_member;
DROP SCHEMA IF EXISTS dcl_07284_schema CASCADE;
CREATE SCHEMA dcl_07284_schema;
CREATE TABLE dcl_07284_schema.dcl_07284_table (id integer, payload text);
GRANT SELECT (payload) ON TABLE dcl_07284_schema.dcl_07284_table TO CURRENT_ROLE;
REVOKE GRANT OPTION FOR SELECT (payload) ON TABLE dcl_07284_schema.dcl_07284_table FROM CURRENT_ROLE GRANTED BY dcl_07284_grantor RESTRICT;
SELECT 'revoke' AS completed_statement, 'column_privilege' AS privilege_scope;
DROP SCHEMA IF EXISTS dcl_07284_schema CASCADE;
DROP OWNED BY dcl_07284_grantee;
DROP OWNED BY dcl_07284_member;
DROP OWNED BY dcl_07284_grantor;
DROP ROLE IF EXISTS dcl_07284_member;
DROP ROLE IF EXISTS dcl_07284_grantor;
DROP ROLE IF EXISTS dcl_07284_grantee;
DROP TABLE IF EXISTS dcl_07284_schema.dcl_07284_table;
