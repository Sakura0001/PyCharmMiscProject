-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_7 (foreign_server) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_7
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=current_role
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
DROP ROLE IF EXISTS "dcl_09876_Grantee";
DROP ROLE IF EXISTS dcl_09876_grantor;
DROP ROLE IF EXISTS dcl_09876_member;
CREATE ROLE "dcl_09876_Grantee";
CREATE ROLE dcl_09876_grantor;
CREATE ROLE dcl_09876_member;
DROP SERVER IF EXISTS dcl_09876_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09876_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_09876_fdw;
CREATE SERVER dcl_09876_server FOREIGN DATA WRAPPER dcl_09876_fdw;
GRANT USAGE ON FOREIGN SERVER dcl_09876_missing_object TO CURRENT_ROLE;
SET ROLE "dcl_09876_Grantee";
REVOKE GRANT OPTION FOR USAGE ON FOREIGN SERVER dcl_09876_missing_object FROM CURRENT_ROLE GRANTED BY dcl_09876_grantor RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
DROP SERVER IF EXISTS dcl_09876_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09876_fdw CASCADE;
DROP OWNED BY "dcl_09876_Grantee";
DROP OWNED BY dcl_09876_member;
DROP OWNED BY dcl_09876_grantor;
DROP ROLE IF EXISTS dcl_09876_member;
DROP ROLE IF EXISTS dcl_09876_grantor;
DROP ROLE IF EXISTS "dcl_09876_Grantee";
