-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_8 (routine) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_8
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=current_user
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=plain_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=effect_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_03368_grantee;
DROP ROLE IF EXISTS dcl_03368_grantor;
DROP ROLE IF EXISTS dcl_03368_member;
CREATE ROLE dcl_03368_grantee;
CREATE ROLE dcl_03368_grantor;
CREATE ROLE dcl_03368_member;
DROP FUNCTION IF EXISTS dcl_03368_function(integer);
CREATE FUNCTION dcl_03368_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
BEGIN;
SET ROLE dcl_03368_grantee;
GRANT EXECUTE ON FUNCTION dcl_03368_missing_object(integer) TO CURRENT_USER GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP FUNCTION IF EXISTS dcl_03368_function(integer);
DROP OWNED BY dcl_03368_grantee;
DROP OWNED BY dcl_03368_member;
DROP OWNED BY dcl_03368_grantor;
DROP ROLE IF EXISTS dcl_03368_member;
DROP ROLE IF EXISTS dcl_03368_grantor;
DROP ROLE IF EXISTS dcl_03368_grantee;
