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
-- factor grantee_shape=role_name
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=quoted_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=error_assertion
-- factor cleanup_mode=drop_objects
DROP TABLE IF EXISTS dcl_07218_schema.dcl_07218_table;
DROP ROLE IF EXISTS "dcl_07218_Grantee";
DROP ROLE IF EXISTS dcl_07218_grantor;
DROP ROLE IF EXISTS dcl_07218_member;
CREATE ROLE "dcl_07218_Grantee";
CREATE ROLE dcl_07218_grantor;
CREATE ROLE dcl_07218_member;
DROP SCHEMA IF EXISTS dcl_07218_schema CASCADE;
CREATE SCHEMA dcl_07218_schema;
CREATE TABLE dcl_07218_schema.dcl_07218_table (id integer, payload text);
GRANT MAINTAIN ON TABLE dcl_07218_missing_object.dcl_07218_table TO "dcl_07218_Grantee";
SET ROLE "dcl_07218_Grantee";
REVOKE INHERIT OPTION FOR MAINTAIN ON TABLE dcl_07218_missing_object.dcl_07218_table FROM "dcl_07218_Grantee" GRANTED BY dcl_07218_grantor RESTRICT;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
DROP SCHEMA IF EXISTS dcl_07218_schema CASCADE;
DROP OWNED BY "dcl_07218_Grantee";
DROP OWNED BY dcl_07218_member;
DROP OWNED BY dcl_07218_grantor;
DROP ROLE IF EXISTS dcl_07218_member;
DROP ROLE IF EXISTS dcl_07218_grantor;
DROP ROLE IF EXISTS "dcl_07218_Grantee";
DROP TABLE IF EXISTS dcl_07218_schema.dcl_07218_table;
