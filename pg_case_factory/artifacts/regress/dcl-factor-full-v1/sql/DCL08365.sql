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
-- factor grantee_shape=session_user
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=missing_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=returned_rows
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_08365_grantor;
DROP ROLE IF EXISTS dcl_08365_member;
CREATE ROLE dcl_08365_grantor;
CREATE ROLE dcl_08365_member;
GRANT CONNECT ON DATABASE dcl_08365_missing_object TO SESSION_USER;
GRANT CONNECT ON DATABASE dcl_08365_missing_object TO dcl_08365_grantor WITH GRANT OPTION;
GRANT dcl_08365_grantor TO dcl_08365_member WITH SET TRUE;
SET ROLE dcl_08365_member;
SET ROLE dcl_08365_grantor;
REVOKE CONNECT ON DATABASE dcl_08365_missing_object FROM SESSION_USER RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'schema_database_tablespace' AS privilege_scope;
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_08365_member;
DROP OWNED BY dcl_08365_grantor;
DROP ROLE IF EXISTS dcl_08365_member;
DROP ROLE IF EXISTS dcl_08365_grantor;
