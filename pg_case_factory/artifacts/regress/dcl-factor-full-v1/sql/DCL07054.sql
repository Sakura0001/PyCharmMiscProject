-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_1 (table) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=current_role
-- factor grant_option_shape=grant_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=missing_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=error_assertion
-- factor cleanup_mode=reset_state
DROP TABLE IF EXISTS dcl_07054_schema.dcl_07054_table;
DROP ROLE IF EXISTS dcl_07054_grantor;
DROP ROLE IF EXISTS dcl_07054_member;
CREATE ROLE dcl_07054_grantor;
CREATE ROLE dcl_07054_member;
DROP SCHEMA IF EXISTS dcl_07054_schema CASCADE;
CREATE SCHEMA dcl_07054_schema;
CREATE TABLE dcl_07054_schema.dcl_07054_table (id integer, payload text);
GRANT EXECUTE ON TABLE dcl_07054_missing_object.dcl_07054_table TO CURRENT_ROLE;
GRANT EXECUTE ON TABLE dcl_07054_missing_object.dcl_07054_table TO dcl_07054_grantor WITH GRANT OPTION;
GRANT dcl_07054_grantor TO dcl_07054_member WITH SET TRUE;
SET ROLE dcl_07054_member;
SET ROLE dcl_07054_grantor;
REVOKE GRANT OPTION FOR EXECUTE ON TABLE dcl_07054_missing_object.dcl_07054_table FROM CURRENT_ROLE RESTRICT;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
RESET ROLE;
RESET ALL;
DROP SCHEMA IF EXISTS dcl_07054_schema CASCADE;
DROP OWNED BY dcl_07054_member;
DROP OWNED BY dcl_07054_grantor;
DROP ROLE IF EXISTS dcl_07054_member;
DROP ROLE IF EXISTS dcl_07054_grantor;
DROP TABLE IF EXISTS dcl_07054_schema.dcl_07054_table;
