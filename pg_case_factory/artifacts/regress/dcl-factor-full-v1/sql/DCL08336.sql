-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_4 (database) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_4
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=public
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
DROP ROLE IF EXISTS dcl_08336_grantee;
DROP ROLE IF EXISTS dcl_08336_grantor;
DROP ROLE IF EXISTS dcl_08336_member;
CREATE ROLE dcl_08336_grantee;
CREATE ROLE dcl_08336_grantor;
CREATE ROLE dcl_08336_member;
GRANT CONNECT ON DATABASE dcl_08336_missing_object TO PUBLIC;
BEGIN;
SET ROLE dcl_08336_grantee;
REVOKE ADMIN OPTION FOR CONNECT ON DATABASE dcl_08336_missing_object FROM PUBLIC GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP OWNED BY dcl_08336_grantee;
DROP OWNED BY dcl_08336_member;
DROP OWNED BY dcl_08336_grantor;
DROP ROLE IF EXISTS dcl_08336_member;
DROP ROLE IF EXISTS dcl_08336_grantor;
DROP ROLE IF EXISTS dcl_08336_grantee;
