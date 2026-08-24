-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_4 (database) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_4
-- factor expected_status=success
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=current_user
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
DROP ROLE IF EXISTS "dcl_01401_Grantee";
DROP ROLE IF EXISTS dcl_01401_grantor;
DROP ROLE IF EXISTS dcl_01401_member;
CREATE ROLE "dcl_01401_Grantee";
CREATE ROLE dcl_01401_grantor;
CREATE ROLE dcl_01401_member;
GRANT CONNECT ON DATABASE dcl_01401_database TO dcl_01401_grantor WITH GRANT OPTION;
SET ROLE dcl_01401_grantor;
GRANT CONNECT ON DATABASE dcl_01401_database TO CURRENT_USER GRANTED BY dcl_01401_grantor;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'schema_database_tablespace' AS privilege_scope;
DROP OWNED BY "dcl_01401_Grantee";
DROP OWNED BY dcl_01401_member;
DROP OWNED BY dcl_01401_grantor;
DROP ROLE IF EXISTS dcl_01401_member;
DROP ROLE IF EXISTS dcl_01401_grantor;
DROP ROLE IF EXISTS "dcl_01401_Grantee";
