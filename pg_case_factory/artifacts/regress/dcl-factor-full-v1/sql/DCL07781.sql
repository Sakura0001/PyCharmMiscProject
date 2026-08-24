-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_3 (sequence) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_3
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=current_role
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=returned_rows
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_07781_grantee;
DROP ROLE IF EXISTS dcl_07781_grantor;
DROP ROLE IF EXISTS dcl_07781_member;
CREATE ROLE dcl_07781_grantee;
CREATE ROLE dcl_07781_grantor;
CREATE ROLE dcl_07781_member;
DROP SEQUENCE IF EXISTS dcl_07781_sequence;
CREATE SEQUENCE dcl_07781_sequence;
GRANT USAGE ON SEQUENCE dcl_07781_missing_object TO CURRENT_ROLE;
BEGIN;
SET ROLE dcl_07781_grantee;
REVOKE INHERIT OPTION FOR USAGE ON SEQUENCE dcl_07781_missing_object FROM CURRENT_ROLE GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'table_privilege' AS privilege_scope;
ROLLBACK;
DROP SEQUENCE IF EXISTS dcl_07781_sequence;
DROP OWNED BY dcl_07781_grantee;
DROP OWNED BY dcl_07781_member;
DROP OWNED BY dcl_07781_grantor;
DROP ROLE IF EXISTS dcl_07781_member;
DROP ROLE IF EXISTS dcl_07781_grantor;
DROP ROLE IF EXISTS dcl_07781_grantee;
