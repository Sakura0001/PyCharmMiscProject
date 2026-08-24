-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_14 (type) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
-- factor expected_status=success
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=current_user
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
DROP ROLE IF EXISTS dcl_12690_grantee;
DROP ROLE IF EXISTS dcl_12690_grantor;
DROP ROLE IF EXISTS dcl_12690_member;
CREATE ROLE dcl_12690_grantee;
CREATE ROLE dcl_12690_grantor;
CREATE ROLE dcl_12690_member;
DROP TYPE IF EXISTS dcl_12690_type;
CREATE TYPE dcl_12690_type AS ENUM ('alpha', 'beta');
GRANT USAGE ON TYPE dcl_12690_type TO CURRENT_USER;
REVOKE GRANT OPTION FOR USAGE ON TYPE dcl_12690_type FROM CURRENT_USER GRANTED BY dcl_12690_grantor RESTRICT;
SELECT 'revoke' AS completed_statement, 'routine_language_type_fdw_server' AS privilege_scope;
DROP TYPE IF EXISTS dcl_12690_type;
DROP OWNED BY dcl_12690_grantee;
DROP OWNED BY dcl_12690_member;
DROP OWNED BY dcl_12690_grantor;
DROP ROLE IF EXISTS dcl_12690_member;
DROP ROLE IF EXISTS dcl_12690_grantor;
DROP ROLE IF EXISTS dcl_12690_grantee;
