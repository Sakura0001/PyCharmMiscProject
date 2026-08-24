-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_2 (column) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=current_role
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
DROP TABLE IF EXISTS dcl_00666_schema.dcl_00666_table;
DROP ROLE IF EXISTS "dcl_00666_Grantee";
DROP ROLE IF EXISTS dcl_00666_grantor;
DROP ROLE IF EXISTS dcl_00666_member;
CREATE ROLE "dcl_00666_Grantee";
CREATE ROLE dcl_00666_grantor;
CREATE ROLE dcl_00666_member;
DROP SCHEMA IF EXISTS dcl_00666_schema CASCADE;
CREATE SCHEMA dcl_00666_schema;
CREATE TABLE dcl_00666_schema.dcl_00666_table (id integer, payload text);
SET ROLE "dcl_00666_Grantee";
GRANT EXECUTE (payload) ON TABLE dcl_00666_missing_object.dcl_00666_table TO CURRENT_ROLE WITH INHERIT TRUE GRANTED BY dcl_00666_grantor;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
DROP SCHEMA IF EXISTS dcl_00666_schema CASCADE;
DROP OWNED BY "dcl_00666_Grantee";
DROP OWNED BY dcl_00666_member;
DROP OWNED BY dcl_00666_grantor;
DROP ROLE IF EXISTS dcl_00666_member;
DROP ROLE IF EXISTS dcl_00666_grantor;
DROP ROLE IF EXISTS "dcl_00666_Grantee";
DROP TABLE IF EXISTS dcl_00666_schema.dcl_00666_table;
