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
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
-- factor grantee_shape=current_user
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=quoted_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=error_assertion
-- factor cleanup_mode=drop_objects
DROP TABLE IF EXISTS dcl_07398_schema.dcl_07398_table;
DROP ROLE IF EXISTS "dcl_07398_Grantee";
DROP ROLE IF EXISTS dcl_07398_grantor;
DROP ROLE IF EXISTS dcl_07398_member;
CREATE ROLE "dcl_07398_Grantee";
CREATE ROLE dcl_07398_grantor;
CREATE ROLE dcl_07398_member;
DROP SCHEMA IF EXISTS dcl_07398_schema CASCADE;
CREATE SCHEMA dcl_07398_schema;
CREATE TABLE dcl_07398_schema.dcl_07398_table (id integer, payload text);
GRANT SELECT (payload) ON TABLE dcl_07398_missing_object.dcl_07398_table TO CURRENT_USER;
SET ROLE "dcl_07398_Grantee";
REVOKE GRANT OPTION FOR SELECT (payload) ON TABLE dcl_07398_missing_object.dcl_07398_table FROM CURRENT_USER GRANTED BY dcl_07398_grantor RESTRICT;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
DROP SCHEMA IF EXISTS dcl_07398_schema CASCADE;
DROP OWNED BY "dcl_07398_Grantee";
DROP OWNED BY dcl_07398_member;
DROP OWNED BY dcl_07398_grantor;
DROP ROLE IF EXISTS dcl_07398_member;
DROP ROLE IF EXISTS dcl_07398_grantor;
DROP ROLE IF EXISTS "dcl_07398_Grantee";
DROP TABLE IF EXISTS dcl_07398_schema.dcl_07398_table;
