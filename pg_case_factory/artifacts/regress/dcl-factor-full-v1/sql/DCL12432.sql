-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_13 (tablespace) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_13
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=role_name
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=quoted_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=effect_query
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_12432_Grantee";
DROP ROLE IF EXISTS dcl_12432_grantor;
DROP ROLE IF EXISTS dcl_12432_member;
CREATE ROLE "dcl_12432_Grantee";
CREATE ROLE dcl_12432_grantor;
CREATE ROLE dcl_12432_member;
GRANT CREATE ON TABLESPACE dcl_12432_missing_object TO "dcl_12432_Grantee";
SET ROLE "dcl_12432_Grantee";
REVOKE GRANT OPTION FOR CREATE ON TABLESPACE dcl_12432_missing_object FROM "dcl_12432_Grantee" GRANTED BY dcl_12432_grantor RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
DROP OWNED BY "dcl_12432_Grantee";
DROP OWNED BY dcl_12432_member;
DROP OWNED BY dcl_12432_grantor;
DROP ROLE IF EXISTS dcl_12432_member;
DROP ROLE IF EXISTS dcl_12432_grantor;
DROP ROLE IF EXISTS "dcl_12432_Grantee";
