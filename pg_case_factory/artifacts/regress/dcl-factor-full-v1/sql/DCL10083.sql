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
-- factor grantee_shape=current_role
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_10083_Grantee";
DROP ROLE IF EXISTS dcl_10083_grantor;
DROP ROLE IF EXISTS dcl_10083_member;
CREATE ROLE "dcl_10083_Grantee";
CREATE ROLE dcl_10083_grantor;
CREATE ROLE dcl_10083_member;
DROP SCHEMA IF EXISTS dcl_10083_schema CASCADE;
CREATE SCHEMA dcl_10083_schema;
CREATE FUNCTION dcl_10083_schema.dcl_10083_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA dcl_10083_missing_object TO CURRENT_ROLE;
SET ROLE "dcl_10083_Grantee";
REVOKE EXECUTE ON ALL FUNCTIONS IN SCHEMA dcl_10083_missing_object FROM CURRENT_ROLE GRANTED BY dcl_10083_grantor RESTRICT;
RESET ROLE;
SELECT has_function_privilege(CURRENT_USER, 'dcl_10083_function(integer)', 'EXECUTE');
DROP SCHEMA IF EXISTS dcl_10083_schema CASCADE;
DROP OWNED BY "dcl_10083_Grantee";
DROP OWNED BY dcl_10083_member;
DROP OWNED BY dcl_10083_grantor;
DROP ROLE IF EXISTS dcl_10083_member;
DROP ROLE IF EXISTS dcl_10083_grantor;
DROP ROLE IF EXISTS "dcl_10083_Grantee";
