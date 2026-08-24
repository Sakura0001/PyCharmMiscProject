-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_7 (foreign_server) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_7
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=session_user
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
DROP ROLE IF EXISTS dcl_09845_grantee;
DROP ROLE IF EXISTS dcl_09845_grantor;
DROP ROLE IF EXISTS dcl_09845_member;
CREATE ROLE dcl_09845_grantee;
CREATE ROLE dcl_09845_grantor;
CREATE ROLE dcl_09845_member;
DROP SERVER IF EXISTS dcl_09845_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09845_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_09845_fdw;
CREATE SERVER dcl_09845_server FOREIGN DATA WRAPPER dcl_09845_fdw;
GRANT USAGE ON FOREIGN SERVER dcl_09845_missing_object TO SESSION_USER;
BEGIN;
SET ROLE dcl_09845_grantee;
REVOKE INHERIT OPTION FOR USAGE ON FOREIGN SERVER dcl_09845_missing_object FROM SESSION_USER GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'role_membership' AS privilege_scope;
ROLLBACK;
DROP SERVER IF EXISTS dcl_09845_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09845_fdw CASCADE;
DROP OWNED BY dcl_09845_grantee;
DROP OWNED BY dcl_09845_member;
DROP OWNED BY dcl_09845_grantor;
DROP ROLE IF EXISTS dcl_09845_member;
DROP ROLE IF EXISTS dcl_09845_grantor;
DROP ROLE IF EXISTS dcl_09845_grantee;
