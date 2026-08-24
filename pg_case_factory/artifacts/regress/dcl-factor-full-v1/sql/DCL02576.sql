-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_6 (foreign_data_wrapper) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_6
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=current_role
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
DROP ROLE IF EXISTS dcl_02576_grantee;
DROP ROLE IF EXISTS dcl_02576_grantor;
DROP ROLE IF EXISTS dcl_02576_member;
CREATE ROLE dcl_02576_grantee;
CREATE ROLE dcl_02576_grantor;
CREATE ROLE dcl_02576_member;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02576_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_02576_fdw;
BEGIN;
SET ROLE dcl_02576_grantee;
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_02576_missing_object TO CURRENT_ROLE GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02576_fdw CASCADE;
DROP OWNED BY dcl_02576_grantee;
DROP OWNED BY dcl_02576_member;
DROP OWNED BY dcl_02576_grantor;
DROP ROLE IF EXISTS dcl_02576_member;
DROP ROLE IF EXISTS dcl_02576_grantor;
DROP ROLE IF EXISTS dcl_02576_grantee;
