-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_12 (schema) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_12
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
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
DROP ROLE IF EXISTS dcl_12164_grantee;
DROP ROLE IF EXISTS dcl_12164_grantor;
DROP ROLE IF EXISTS dcl_12164_member;
CREATE ROLE dcl_12164_grantee;
CREATE ROLE dcl_12164_grantor;
CREATE ROLE dcl_12164_member;
DROP SCHEMA IF EXISTS dcl_12164_schema CASCADE;
CREATE SCHEMA dcl_12164_schema;
GRANT USAGE ON SCHEMA dcl_12164_missing_object TO dcl_12164_grantee;
BEGIN;
SET ROLE dcl_12164_grantee;
REVOKE ADMIN OPTION FOR USAGE ON SCHEMA dcl_12164_missing_object FROM dcl_12164_grantee GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP SCHEMA IF EXISTS dcl_12164_schema CASCADE;
DROP OWNED BY dcl_12164_grantee;
DROP OWNED BY dcl_12164_member;
DROP OWNED BY dcl_12164_grantor;
DROP ROLE IF EXISTS dcl_12164_member;
DROP ROLE IF EXISTS dcl_12164_grantor;
DROP ROLE IF EXISTS dcl_12164_grantee;
