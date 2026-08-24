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
-- factor grantee_shape=session_user
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=member_role
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS "dcl_08191_Grantee";
DROP ROLE IF EXISTS dcl_08191_grantor;
DROP ROLE IF EXISTS dcl_08191_member;
CREATE ROLE "dcl_08191_Grantee";
CREATE ROLE dcl_08191_grantor;
CREATE ROLE dcl_08191_member;
GRANT CONNECT ON DATABASE dcl_08191_database TO SESSION_USER;
GRANT CONNECT ON DATABASE dcl_08191_database TO dcl_08191_grantor WITH GRANT OPTION;
SET ROLE dcl_08191_grantor;
REVOKE CONNECT ON DATABASE dcl_08191_database FROM SESSION_USER RESTRICT;
RESET ROLE;
SELECT has_database_privilege(CURRENT_USER, 'dcl_08191_database', 'CONNECT');
RESET ROLE;
RESET ALL;
DROP OWNED BY "dcl_08191_Grantee";
DROP OWNED BY dcl_08191_member;
DROP OWNED BY dcl_08191_grantor;
DROP ROLE IF EXISTS dcl_08191_member;
DROP ROLE IF EXISTS dcl_08191_grantor;
DROP ROLE IF EXISTS "dcl_08191_Grantee";
