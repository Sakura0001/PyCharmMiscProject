-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_12 (schema) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_12
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=current_role
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=returned_rows
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_12125_grantee;
DROP ROLE IF EXISTS dcl_12125_grantor;
DROP ROLE IF EXISTS dcl_12125_member;
CREATE ROLE dcl_12125_grantee;
CREATE ROLE dcl_12125_grantor;
CREATE ROLE dcl_12125_member;
DROP SCHEMA IF EXISTS dcl_12125_schema CASCADE;
CREATE SCHEMA dcl_12125_schema;
GRANT USAGE ON SCHEMA dcl_12125_missing_object TO CURRENT_ROLE;
BEGIN;
SET ROLE dcl_12125_grantee;
REVOKE GRANT OPTION FOR USAGE ON SCHEMA dcl_12125_missing_object FROM CURRENT_ROLE GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'parameter_privilege' AS privilege_scope;
ROLLBACK;
DROP SCHEMA IF EXISTS dcl_12125_schema CASCADE;
DROP OWNED BY dcl_12125_grantee;
DROP OWNED BY dcl_12125_member;
DROP OWNED BY dcl_12125_grantor;
DROP ROLE IF EXISTS dcl_12125_member;
DROP ROLE IF EXISTS dcl_12125_grantor;
DROP ROLE IF EXISTS dcl_12125_grantee;
