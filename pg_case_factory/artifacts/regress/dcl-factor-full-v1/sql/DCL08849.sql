-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_5 (domain) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_5
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=public
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
DROP ROLE IF EXISTS dcl_08849_grantee;
DROP ROLE IF EXISTS dcl_08849_grantor;
DROP ROLE IF EXISTS dcl_08849_member;
CREATE ROLE dcl_08849_grantee;
CREATE ROLE dcl_08849_grantor;
CREATE ROLE dcl_08849_member;
DROP DOMAIN IF EXISTS dcl_08849_domain;
CREATE DOMAIN dcl_08849_domain AS text;
GRANT USAGE ON DOMAIN dcl_08849_missing_object TO PUBLIC;
BEGIN;
SET ROLE dcl_08849_grantee;
REVOKE INHERIT OPTION FOR USAGE ON DOMAIN dcl_08849_missing_object FROM PUBLIC GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'routine_language_type_fdw_server' AS privilege_scope;
ROLLBACK;
DROP DOMAIN IF EXISTS dcl_08849_domain;
DROP OWNED BY dcl_08849_grantee;
DROP OWNED BY dcl_08849_member;
DROP OWNED BY dcl_08849_grantor;
DROP ROLE IF EXISTS dcl_08849_member;
DROP ROLE IF EXISTS dcl_08849_grantor;
DROP ROLE IF EXISTS dcl_08849_grantee;
