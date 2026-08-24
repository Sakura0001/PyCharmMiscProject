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
-- factor grantee_shape=session_user
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=none
-- factor ownership_boundary=owner
-- factor verification_mode=returned_rows
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS dcl_01410_grantee;
DROP ROLE IF EXISTS dcl_01410_grantor;
DROP ROLE IF EXISTS dcl_01410_member;
CREATE ROLE dcl_01410_grantee;
CREATE ROLE dcl_01410_grantor;
CREATE ROLE dcl_01410_member;
GRANT CONNECT ON DATABASE dcl_01410_database TO SESSION_USER WITH GRANT OPTION GRANTED BY dcl_01410_grantor;
SELECT 'grant' AS completed_statement, 'schema_database_tablespace' AS privilege_scope;
DROP OWNED BY dcl_01410_grantee;
DROP OWNED BY dcl_01410_member;
DROP OWNED BY dcl_01410_grantor;
DROP ROLE IF EXISTS dcl_01410_member;
DROP ROLE IF EXISTS dcl_01410_grantor;
DROP ROLE IF EXISTS dcl_01410_grantee;
