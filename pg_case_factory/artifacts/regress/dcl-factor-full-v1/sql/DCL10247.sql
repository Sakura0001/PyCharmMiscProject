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
-- factor grantee_shape=role_name
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_10247_grantee;
DROP ROLE IF EXISTS dcl_10247_grantor;
DROP ROLE IF EXISTS dcl_10247_member;
CREATE ROLE dcl_10247_grantee;
CREATE ROLE dcl_10247_grantor;
CREATE ROLE dcl_10247_member;
DROP SCHEMA IF EXISTS dcl_10247_schema CASCADE;
CREATE SCHEMA dcl_10247_schema;
CREATE FUNCTION dcl_10247_schema.dcl_10247_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA dcl_10247_missing_object TO dcl_10247_grantee;
BEGIN;
SET ROLE dcl_10247_grantee;
REVOKE INHERIT OPTION FOR EXECUTE ON ALL FUNCTIONS IN SCHEMA dcl_10247_missing_object FROM dcl_10247_grantee GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT has_function_privilege(CURRENT_USER, 'dcl_10247_function(integer)', 'EXECUTE');
ROLLBACK;
DROP SCHEMA IF EXISTS dcl_10247_schema CASCADE;
DROP OWNED BY dcl_10247_grantee;
DROP OWNED BY dcl_10247_member;
DROP OWNED BY dcl_10247_grantor;
DROP ROLE IF EXISTS dcl_10247_member;
DROP ROLE IF EXISTS dcl_10247_grantor;
DROP ROLE IF EXISTS dcl_10247_grantee;
