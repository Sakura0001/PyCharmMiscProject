-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_12 (schema) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_12
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=role_name
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
DROP ROLE IF EXISTS dcl_05192_grantee;
DROP ROLE IF EXISTS dcl_05192_grantor;
DROP ROLE IF EXISTS dcl_05192_member;
CREATE ROLE dcl_05192_grantee;
CREATE ROLE dcl_05192_grantor;
CREATE ROLE dcl_05192_member;
DROP SCHEMA IF EXISTS dcl_05192_schema CASCADE;
CREATE SCHEMA dcl_05192_schema;
BEGIN;
SET ROLE dcl_05192_grantee;
GRANT USAGE ON SCHEMA dcl_05192_missing_object TO dcl_05192_grantee GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP SCHEMA IF EXISTS dcl_05192_schema CASCADE;
DROP OWNED BY dcl_05192_grantee;
DROP OWNED BY dcl_05192_member;
DROP OWNED BY dcl_05192_grantor;
DROP ROLE IF EXISTS dcl_05192_member;
DROP ROLE IF EXISTS dcl_05192_grantor;
DROP ROLE IF EXISTS dcl_05192_grantee;
