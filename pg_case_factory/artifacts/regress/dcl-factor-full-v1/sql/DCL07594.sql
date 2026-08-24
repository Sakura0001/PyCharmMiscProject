-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_2 (column) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=session_user
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=missing_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=error_assertion
-- factor cleanup_mode=reset_state
DROP TABLE IF EXISTS dcl_07594_schema.dcl_07594_table;
DROP ROLE IF EXISTS dcl_07594_grantor;
DROP ROLE IF EXISTS dcl_07594_member;
CREATE ROLE dcl_07594_grantor;
CREATE ROLE dcl_07594_member;
DROP SCHEMA IF EXISTS dcl_07594_schema CASCADE;
CREATE SCHEMA dcl_07594_schema;
CREATE TABLE dcl_07594_schema.dcl_07594_table (id integer, payload text);
GRANT EXECUTE ON TABLE dcl_07594_missing_object.dcl_07594_table TO SESSION_USER;
GRANT EXECUTE ON TABLE dcl_07594_missing_object.dcl_07594_table TO dcl_07594_grantor WITH GRANT OPTION;
GRANT dcl_07594_grantor TO dcl_07594_member WITH SET TRUE;
SET ROLE dcl_07594_member;
SET ROLE dcl_07594_grantor;
REVOKE INHERIT OPTION FOR EXECUTE ON TABLE dcl_07594_missing_object.dcl_07594_table FROM SESSION_USER RESTRICT;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
RESET ROLE;
RESET ALL;
DROP SCHEMA IF EXISTS dcl_07594_schema CASCADE;
DROP OWNED BY dcl_07594_member;
DROP OWNED BY dcl_07594_grantor;
DROP ROLE IF EXISTS dcl_07594_member;
DROP ROLE IF EXISTS dcl_07594_grantor;
DROP TABLE IF EXISTS dcl_07594_schema.dcl_07594_table;
