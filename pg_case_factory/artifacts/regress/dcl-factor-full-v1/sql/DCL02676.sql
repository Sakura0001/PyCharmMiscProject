-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_6 (foreign_data_wrapper) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_6
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
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
DROP ROLE IF EXISTS "dcl_02676_Grantee";
DROP ROLE IF EXISTS dcl_02676_grantor;
DROP ROLE IF EXISTS dcl_02676_member;
CREATE ROLE "dcl_02676_Grantee";
CREATE ROLE dcl_02676_grantor;
CREATE ROLE dcl_02676_member;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02676_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_02676_fdw;
SET ROLE "dcl_02676_Grantee";
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_02676_missing_object TO "dcl_02676_Grantee" WITH GRANT OPTION GRANTED BY dcl_02676_grantor;
RESET ROLE;
SELECT true AS privilege_effect_observed;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02676_fdw CASCADE;
DROP OWNED BY "dcl_02676_Grantee";
DROP OWNED BY dcl_02676_member;
DROP OWNED BY dcl_02676_grantor;
DROP ROLE IF EXISTS dcl_02676_member;
DROP ROLE IF EXISTS dcl_02676_grantor;
DROP ROLE IF EXISTS "dcl_02676_Grantee";
