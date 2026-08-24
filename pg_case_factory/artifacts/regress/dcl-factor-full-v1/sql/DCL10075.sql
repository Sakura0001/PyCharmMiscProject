-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_8 (routine) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_8
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
-- factor grantee_shape=public
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
DROP ROLE IF EXISTS dcl_10075_grantor;
DROP ROLE IF EXISTS dcl_10075_member;
CREATE ROLE dcl_10075_grantor;
CREATE ROLE dcl_10075_member;
DROP SCHEMA IF EXISTS dcl_10075_schema CASCADE;
CREATE SCHEMA dcl_10075_schema;
CREATE FUNCTION dcl_10075_schema.dcl_10075_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA dcl_10075_missing_object TO PUBLIC;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA dcl_10075_missing_object TO dcl_10075_grantor WITH GRANT OPTION;
GRANT dcl_10075_grantor TO dcl_10075_member WITH SET TRUE;
SET ROLE dcl_10075_member;
SET ROLE dcl_10075_grantor;
REVOKE ADMIN OPTION FOR EXECUTE ON ALL FUNCTIONS IN SCHEMA dcl_10075_missing_object FROM PUBLIC RESTRICT;
RESET ROLE;
SELECT has_function_privilege(CURRENT_USER, 'dcl_10075_function(integer)', 'EXECUTE');
RESET ROLE;
RESET ALL;
DROP SCHEMA IF EXISTS dcl_10075_schema CASCADE;
DROP OWNED BY dcl_10075_member;
DROP OWNED BY dcl_10075_grantor;
DROP ROLE IF EXISTS dcl_10075_member;
DROP ROLE IF EXISTS dcl_10075_grantor;
