-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_1 (table) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=current_role
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
DROP TABLE IF EXISTS dcl_00090_schema.dcl_00090_table;
DROP ROLE IF EXISTS "dcl_00090_Grantee";
DROP ROLE IF EXISTS dcl_00090_grantor;
DROP ROLE IF EXISTS dcl_00090_member;
CREATE ROLE "dcl_00090_Grantee";
CREATE ROLE dcl_00090_grantor;
CREATE ROLE dcl_00090_member;
DROP SCHEMA IF EXISTS dcl_00090_schema CASCADE;
CREATE SCHEMA dcl_00090_schema;
CREATE TABLE dcl_00090_schema.dcl_00090_table (id integer, payload text);
SET ROLE "dcl_00090_Grantee";
GRANT SELECT ON TABLE dcl_00090_missing_object.dcl_00090_table TO CURRENT_ROLE WITH GRANT OPTION GRANTED BY dcl_00090_grantor;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
DROP SCHEMA IF EXISTS dcl_00090_schema CASCADE;
DROP OWNED BY "dcl_00090_Grantee";
DROP OWNED BY dcl_00090_member;
DROP OWNED BY dcl_00090_grantor;
DROP ROLE IF EXISTS dcl_00090_member;
DROP ROLE IF EXISTS dcl_00090_grantor;
DROP ROLE IF EXISTS "dcl_00090_Grantee";
DROP TABLE IF EXISTS dcl_00090_schema.dcl_00090_table;
