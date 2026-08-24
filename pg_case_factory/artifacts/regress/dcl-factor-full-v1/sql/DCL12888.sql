-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_14 (type) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
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
DROP ROLE IF EXISTS "dcl_12888_Grantee";
DROP ROLE IF EXISTS dcl_12888_grantor;
DROP ROLE IF EXISTS dcl_12888_member;
CREATE ROLE "dcl_12888_Grantee";
CREATE ROLE dcl_12888_grantor;
CREATE ROLE dcl_12888_member;
DROP TYPE IF EXISTS dcl_12888_type;
CREATE TYPE dcl_12888_type AS ENUM ('alpha', 'beta');
GRANT USAGE ON TYPE dcl_12888_missing_object TO "dcl_12888_Grantee";
SET ROLE "dcl_12888_Grantee";
REVOKE INHERIT OPTION FOR USAGE ON TYPE dcl_12888_missing_object FROM "dcl_12888_Grantee" GRANTED BY dcl_12888_grantor RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
DROP TYPE IF EXISTS dcl_12888_type;
DROP OWNED BY "dcl_12888_Grantee";
DROP OWNED BY dcl_12888_member;
DROP OWNED BY dcl_12888_grantor;
DROP ROLE IF EXISTS dcl_12888_member;
DROP ROLE IF EXISTS dcl_12888_grantor;
DROP ROLE IF EXISTS "dcl_12888_Grantee";
