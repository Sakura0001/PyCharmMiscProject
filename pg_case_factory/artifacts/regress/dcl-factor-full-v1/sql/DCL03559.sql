-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_8 (routine) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_8
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=session_user
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=missing_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_03559_grantor;
DROP ROLE IF EXISTS dcl_03559_member;
CREATE ROLE dcl_03559_grantor;
CREATE ROLE dcl_03559_member;
DROP SCHEMA IF EXISTS dcl_03559_schema CASCADE;
CREATE SCHEMA dcl_03559_schema;
CREATE FUNCTION dcl_03559_schema.dcl_03559_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA dcl_03559_missing_object TO dcl_03559_grantor WITH GRANT OPTION;
GRANT dcl_03559_grantor TO dcl_03559_member WITH SET TRUE;
SET ROLE dcl_03559_member;
SET ROLE dcl_03559_grantor;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA dcl_03559_missing_object TO SESSION_USER;
RESET ROLE;
SELECT has_function_privilege(CURRENT_USER, 'dcl_03559_function(integer)', 'EXECUTE');
RESET ROLE;
RESET ALL;
DROP SCHEMA IF EXISTS dcl_03559_schema CASCADE;
DROP OWNED BY dcl_03559_member;
DROP OWNED BY dcl_03559_grantor;
DROP ROLE IF EXISTS dcl_03559_member;
DROP ROLE IF EXISTS dcl_03559_grantor;
