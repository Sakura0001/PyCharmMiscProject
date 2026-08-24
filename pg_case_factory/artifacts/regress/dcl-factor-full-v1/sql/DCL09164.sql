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
-- factor grantee_shape=role_name
-- factor grant_option_shape=admin_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=plain_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=effect_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_09164_grantee;
DROP ROLE IF EXISTS dcl_09164_grantor;
DROP ROLE IF EXISTS dcl_09164_member;
CREATE ROLE dcl_09164_grantee;
CREATE ROLE dcl_09164_grantor;
CREATE ROLE dcl_09164_member;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09164_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_09164_fdw;
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_09164_missing_object TO dcl_09164_grantee;
BEGIN;
SET ROLE dcl_09164_grantee;
REVOKE ADMIN OPTION FOR USAGE ON FOREIGN DATA WRAPPER dcl_09164_missing_object FROM dcl_09164_grantee GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09164_fdw CASCADE;
DROP OWNED BY dcl_09164_grantee;
DROP OWNED BY dcl_09164_member;
DROP OWNED BY dcl_09164_grantor;
DROP ROLE IF EXISTS dcl_09164_member;
DROP ROLE IF EXISTS dcl_09164_grantor;
DROP ROLE IF EXISTS dcl_09164_grantee;
