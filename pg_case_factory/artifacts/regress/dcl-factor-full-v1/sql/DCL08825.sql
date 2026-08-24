-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_5 (domain) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_5
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
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
DROP ROLE IF EXISTS dcl_08825_grantee;
DROP ROLE IF EXISTS dcl_08825_grantor;
DROP ROLE IF EXISTS dcl_08825_member;
CREATE ROLE dcl_08825_grantee;
CREATE ROLE dcl_08825_grantor;
CREATE ROLE dcl_08825_member;
DROP DOMAIN IF EXISTS dcl_08825_domain;
CREATE DOMAIN dcl_08825_domain AS text;
GRANT USAGE ON DOMAIN dcl_08825_missing_object TO SESSION_USER;
BEGIN;
SET ROLE dcl_08825_grantee;
REVOKE INHERIT OPTION FOR USAGE ON DOMAIN dcl_08825_missing_object FROM SESSION_USER GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'schema_database_tablespace' AS privilege_scope;
ROLLBACK;
DROP DOMAIN IF EXISTS dcl_08825_domain;
DROP OWNED BY dcl_08825_grantee;
DROP OWNED BY dcl_08825_member;
DROP OWNED BY dcl_08825_grantor;
DROP ROLE IF EXISTS dcl_08825_member;
DROP ROLE IF EXISTS dcl_08825_grantor;
DROP ROLE IF EXISTS dcl_08825_grantee;
