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
-- factor grantee_shape=current_role
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=member_role
-- factor verification_mode=returned_rows
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_08181_Grantee";
DROP ROLE IF EXISTS dcl_08181_grantor;
DROP ROLE IF EXISTS dcl_08181_member;
CREATE ROLE "dcl_08181_Grantee";
CREATE ROLE dcl_08181_grantor;
CREATE ROLE dcl_08181_member;
GRANT CONNECT ON DATABASE dcl_08181_database TO CURRENT_ROLE;
GRANT CONNECT ON DATABASE dcl_08181_database TO dcl_08181_grantor WITH GRANT OPTION;
SET ROLE dcl_08181_grantor;
REVOKE CONNECT ON DATABASE dcl_08181_database FROM CURRENT_ROLE GRANTED BY dcl_08181_grantor RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'schema_database_tablespace' AS privilege_scope;
DROP OWNED BY "dcl_08181_Grantee";
DROP OWNED BY dcl_08181_member;
DROP OWNED BY dcl_08181_grantor;
DROP ROLE IF EXISTS dcl_08181_member;
DROP ROLE IF EXISTS dcl_08181_grantor;
DROP ROLE IF EXISTS "dcl_08181_Grantee";
