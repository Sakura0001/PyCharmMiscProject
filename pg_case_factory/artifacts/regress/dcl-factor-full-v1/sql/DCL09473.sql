-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_6 (foreign_data_wrapper) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_6
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
-- factor grantee_shape=public
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
DROP ROLE IF EXISTS dcl_09473_grantee;
DROP ROLE IF EXISTS dcl_09473_grantor;
DROP ROLE IF EXISTS dcl_09473_member;
CREATE ROLE dcl_09473_grantee;
CREATE ROLE dcl_09473_grantor;
CREATE ROLE dcl_09473_member;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09473_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_09473_fdw;
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_09473_missing_object TO PUBLIC;
BEGIN;
SET ROLE dcl_09473_grantee;
REVOKE GRANT OPTION FOR USAGE ON FOREIGN DATA WRAPPER dcl_09473_missing_object FROM PUBLIC GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'table_maintain' AS privilege_scope;
ROLLBACK;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09473_fdw CASCADE;
DROP OWNED BY dcl_09473_grantee;
DROP OWNED BY dcl_09473_member;
DROP OWNED BY dcl_09473_grantor;
DROP ROLE IF EXISTS dcl_09473_member;
DROP ROLE IF EXISTS dcl_09473_grantor;
DROP ROLE IF EXISTS dcl_09473_grantee;
