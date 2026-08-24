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
-- factor grantee_shape=current_user
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
DROP ROLE IF EXISTS dcl_12197_grantee;
DROP ROLE IF EXISTS dcl_12197_grantor;
DROP ROLE IF EXISTS dcl_12197_member;
CREATE ROLE dcl_12197_grantee;
CREATE ROLE dcl_12197_grantor;
CREATE ROLE dcl_12197_member;
DROP SCHEMA IF EXISTS dcl_12197_schema CASCADE;
CREATE SCHEMA dcl_12197_schema;
GRANT USAGE ON SCHEMA dcl_12197_missing_object TO CURRENT_USER;
BEGIN;
SET ROLE dcl_12197_grantee;
REVOKE GRANT OPTION FOR USAGE ON SCHEMA dcl_12197_missing_object FROM CURRENT_USER GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'table_maintain' AS privilege_scope;
ROLLBACK;
DROP SCHEMA IF EXISTS dcl_12197_schema CASCADE;
DROP OWNED BY dcl_12197_grantee;
DROP OWNED BY dcl_12197_member;
DROP OWNED BY dcl_12197_grantor;
DROP ROLE IF EXISTS dcl_12197_member;
DROP ROLE IF EXISTS dcl_12197_grantor;
DROP ROLE IF EXISTS dcl_12197_grantee;
