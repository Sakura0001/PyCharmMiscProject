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
-- factor expected_status=success
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=public
-- factor grant_option_shape=grant_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=none
-- factor ownership_boundary=owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_08176_grantee;
DROP ROLE IF EXISTS dcl_08176_grantor;
DROP ROLE IF EXISTS dcl_08176_member;
CREATE ROLE dcl_08176_grantee;
CREATE ROLE dcl_08176_grantor;
CREATE ROLE dcl_08176_member;
GRANT CONNECT ON DATABASE dcl_08176_database TO PUBLIC;
REVOKE GRANT OPTION FOR CONNECT ON DATABASE dcl_08176_database FROM PUBLIC RESTRICT;
SELECT has_database_privilege(CURRENT_USER, 'dcl_08176_database', 'CONNECT');
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_08176_grantee;
DROP OWNED BY dcl_08176_member;
DROP OWNED BY dcl_08176_grantor;
DROP ROLE IF EXISTS dcl_08176_member;
DROP ROLE IF EXISTS dcl_08176_grantor;
DROP ROLE IF EXISTS dcl_08176_grantee;
