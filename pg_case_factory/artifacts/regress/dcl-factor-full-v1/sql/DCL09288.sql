-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_6 (foreign_data_wrapper) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_6
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
DROP ROLE IF EXISTS "dcl_09288_Grantee";
DROP ROLE IF EXISTS dcl_09288_grantor;
DROP ROLE IF EXISTS dcl_09288_member;
CREATE ROLE "dcl_09288_Grantee";
CREATE ROLE dcl_09288_grantor;
CREATE ROLE dcl_09288_member;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09288_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_09288_fdw;
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_09288_missing_object TO "dcl_09288_Grantee";
SET ROLE "dcl_09288_Grantee";
REVOKE INHERIT OPTION FOR USAGE ON FOREIGN DATA WRAPPER dcl_09288_missing_object FROM "dcl_09288_Grantee" GRANTED BY dcl_09288_grantor RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09288_fdw CASCADE;
DROP OWNED BY "dcl_09288_Grantee";
DROP OWNED BY dcl_09288_member;
DROP OWNED BY dcl_09288_grantor;
DROP ROLE IF EXISTS dcl_09288_member;
DROP ROLE IF EXISTS dcl_09288_grantor;
DROP ROLE IF EXISTS "dcl_09288_Grantee";
