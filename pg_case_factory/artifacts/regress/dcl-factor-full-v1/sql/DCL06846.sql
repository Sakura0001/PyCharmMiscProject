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
-- factor expected_status=success
-- factor privilege_scope=table_maintain
-- factor grantee_shape=session_user
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
DROP TABLE IF EXISTS dcl_06846_schema.dcl_06846_table;
DROP ROLE IF EXISTS dcl_06846_grantee;
DROP ROLE IF EXISTS dcl_06846_grantor;
DROP ROLE IF EXISTS dcl_06846_member;
CREATE ROLE dcl_06846_grantee;
CREATE ROLE dcl_06846_grantor;
CREATE ROLE dcl_06846_member;
DROP SCHEMA IF EXISTS dcl_06846_schema CASCADE;
CREATE SCHEMA dcl_06846_schema;
CREATE TABLE dcl_06846_schema.dcl_06846_table (id integer, payload text);
GRANT MAINTAIN ON TABLE dcl_06846_schema.dcl_06846_table TO SESSION_USER;
REVOKE GRANT OPTION FOR MAINTAIN ON TABLE dcl_06846_schema.dcl_06846_table FROM SESSION_USER GRANTED BY dcl_06846_grantor RESTRICT;
SELECT 'revoke' AS completed_statement, 'table_maintain' AS privilege_scope;
DROP SCHEMA IF EXISTS dcl_06846_schema CASCADE;
DROP OWNED BY dcl_06846_grantee;
DROP OWNED BY dcl_06846_member;
DROP OWNED BY dcl_06846_grantor;
DROP ROLE IF EXISTS dcl_06846_member;
DROP ROLE IF EXISTS dcl_06846_grantor;
DROP ROLE IF EXISTS dcl_06846_grantee;
DROP TABLE IF EXISTS dcl_06846_schema.dcl_06846_table;
