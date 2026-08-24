-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_8 (routine) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_8
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=session_user
-- factor grant_option_shape=admin_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=missing_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_10171_grantor;
DROP ROLE IF EXISTS dcl_10171_member;
CREATE ROLE dcl_10171_grantor;
CREATE ROLE dcl_10171_member;
DROP SCHEMA IF EXISTS dcl_10171_schema CASCADE;
CREATE SCHEMA dcl_10171_schema;
CREATE FUNCTION dcl_10171_schema.dcl_10171_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA dcl_10171_missing_object TO SESSION_USER;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA dcl_10171_missing_object TO dcl_10171_grantor WITH GRANT OPTION;
GRANT dcl_10171_grantor TO dcl_10171_member WITH SET TRUE;
SET ROLE dcl_10171_member;
SET ROLE dcl_10171_grantor;
REVOKE ADMIN OPTION FOR EXECUTE ON ALL FUNCTIONS IN SCHEMA dcl_10171_missing_object FROM SESSION_USER RESTRICT;
RESET ROLE;
SELECT has_function_privilege(CURRENT_USER, 'dcl_10171_function(integer)', 'EXECUTE');
RESET ROLE;
RESET ALL;
DROP SCHEMA IF EXISTS dcl_10171_schema CASCADE;
DROP OWNED BY dcl_10171_member;
DROP OWNED BY dcl_10171_grantor;
DROP ROLE IF EXISTS dcl_10171_member;
DROP ROLE IF EXISTS dcl_10171_grantor;
