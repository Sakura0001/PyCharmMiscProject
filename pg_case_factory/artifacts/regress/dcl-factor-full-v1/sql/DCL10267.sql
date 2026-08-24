-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_8 (routine) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_8
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=current_role
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
DROP ROLE IF EXISTS dcl_10267_grantor;
DROP ROLE IF EXISTS dcl_10267_member;
CREATE ROLE dcl_10267_grantor;
CREATE ROLE dcl_10267_member;
DROP SCHEMA IF EXISTS dcl_10267_schema CASCADE;
CREATE SCHEMA dcl_10267_schema;
CREATE FUNCTION dcl_10267_schema.dcl_10267_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA dcl_10267_missing_object TO CURRENT_ROLE;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA dcl_10267_missing_object TO dcl_10267_grantor WITH GRANT OPTION;
GRANT dcl_10267_grantor TO dcl_10267_member WITH SET TRUE;
SET ROLE dcl_10267_member;
SET ROLE dcl_10267_grantor;
REVOKE ADMIN OPTION FOR EXECUTE ON ALL FUNCTIONS IN SCHEMA dcl_10267_missing_object FROM CURRENT_ROLE RESTRICT;
RESET ROLE;
SELECT has_function_privilege(CURRENT_USER, 'dcl_10267_function(integer)', 'EXECUTE');
RESET ROLE;
RESET ALL;
DROP SCHEMA IF EXISTS dcl_10267_schema CASCADE;
DROP OWNED BY dcl_10267_member;
DROP OWNED BY dcl_10267_grantor;
DROP ROLE IF EXISTS dcl_10267_member;
DROP ROLE IF EXISTS dcl_10267_grantor;
