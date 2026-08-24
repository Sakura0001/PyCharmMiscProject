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
-- factor grantee_shape=public
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_03527_grantee;
DROP ROLE IF EXISTS dcl_03527_grantor;
DROP ROLE IF EXISTS dcl_03527_member;
CREATE ROLE dcl_03527_grantee;
CREATE ROLE dcl_03527_grantor;
CREATE ROLE dcl_03527_member;
DROP SCHEMA IF EXISTS dcl_03527_schema CASCADE;
CREATE SCHEMA dcl_03527_schema;
CREATE FUNCTION dcl_03527_schema.dcl_03527_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
BEGIN;
SET ROLE dcl_03527_grantee;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA dcl_03527_missing_object TO PUBLIC WITH GRANT OPTION GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT has_function_privilege(CURRENT_USER, 'dcl_03527_function(integer)', 'EXECUTE');
ROLLBACK;
DROP SCHEMA IF EXISTS dcl_03527_schema CASCADE;
DROP OWNED BY dcl_03527_grantee;
DROP OWNED BY dcl_03527_member;
DROP OWNED BY dcl_03527_grantor;
DROP ROLE IF EXISTS dcl_03527_member;
DROP ROLE IF EXISTS dcl_03527_grantor;
DROP ROLE IF EXISTS dcl_03527_grantee;
