-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_6 (foreign_data_wrapper) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_6
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
-- factor grantee_shape=public
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
DROP ROLE IF EXISTS "dcl_09180_Grantee";
DROP ROLE IF EXISTS dcl_09180_grantor;
DROP ROLE IF EXISTS dcl_09180_member;
CREATE ROLE "dcl_09180_Grantee";
CREATE ROLE dcl_09180_grantor;
CREATE ROLE dcl_09180_member;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09180_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_09180_fdw;
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_09180_missing_object TO PUBLIC;
SET ROLE "dcl_09180_Grantee";
REVOKE INHERIT OPTION FOR USAGE ON FOREIGN DATA WRAPPER dcl_09180_missing_object FROM PUBLIC GRANTED BY dcl_09180_grantor RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09180_fdw CASCADE;
DROP OWNED BY "dcl_09180_Grantee";
DROP OWNED BY dcl_09180_member;
DROP OWNED BY dcl_09180_grantor;
DROP ROLE IF EXISTS dcl_09180_member;
DROP ROLE IF EXISTS dcl_09180_grantor;
DROP ROLE IF EXISTS "dcl_09180_Grantee";
