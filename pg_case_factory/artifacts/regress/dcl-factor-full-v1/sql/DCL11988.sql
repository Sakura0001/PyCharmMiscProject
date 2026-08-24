-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_12 (schema) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_12
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=role_name
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=quoted_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=effect_query
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_11988_Grantee";
DROP ROLE IF EXISTS dcl_11988_grantor;
DROP ROLE IF EXISTS dcl_11988_member;
CREATE ROLE "dcl_11988_Grantee";
CREATE ROLE dcl_11988_grantor;
CREATE ROLE dcl_11988_member;
DROP SCHEMA IF EXISTS dcl_11988_schema CASCADE;
CREATE SCHEMA dcl_11988_schema;
GRANT USAGE ON SCHEMA dcl_11988_missing_object TO "dcl_11988_Grantee";
SET ROLE "dcl_11988_Grantee";
REVOKE INHERIT OPTION FOR USAGE ON SCHEMA dcl_11988_missing_object FROM "dcl_11988_Grantee" GRANTED BY dcl_11988_grantor RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
DROP SCHEMA IF EXISTS dcl_11988_schema CASCADE;
DROP OWNED BY "dcl_11988_Grantee";
DROP OWNED BY dcl_11988_member;
DROP OWNED BY dcl_11988_grantor;
DROP ROLE IF EXISTS dcl_11988_member;
DROP ROLE IF EXISTS dcl_11988_grantor;
DROP ROLE IF EXISTS "dcl_11988_Grantee";
