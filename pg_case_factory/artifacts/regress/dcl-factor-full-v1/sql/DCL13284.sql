-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_15 (role_membership) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_15
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
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
DROP ROLE IF EXISTS "dcl_13284_Grantee";
DROP ROLE IF EXISTS dcl_13284_grantor;
DROP ROLE IF EXISTS dcl_13284_member;
CREATE ROLE "dcl_13284_Grantee";
CREATE ROLE dcl_13284_grantor;
CREATE ROLE dcl_13284_member;
SET ROLE "dcl_13284_Grantee";
REVOKE SET OPTION FOR dcl_13284_missing_member FROM "dcl_13284_Grantee" GRANTED BY dcl_13284_grantor RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
DROP OWNED BY "dcl_13284_Grantee";
DROP OWNED BY dcl_13284_member;
DROP OWNED BY dcl_13284_grantor;
DROP ROLE IF EXISTS dcl_13284_member;
DROP ROLE IF EXISTS dcl_13284_grantor;
DROP ROLE IF EXISTS "dcl_13284_Grantee";
