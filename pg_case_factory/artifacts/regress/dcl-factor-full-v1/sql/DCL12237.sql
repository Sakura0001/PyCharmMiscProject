-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_13 (tablespace) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_13
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
DROP ROLE IF EXISTS "dcl_12237_Grantee";
DROP ROLE IF EXISTS dcl_12237_grantor;
DROP ROLE IF EXISTS dcl_12237_member;
CREATE ROLE "dcl_12237_Grantee";
CREATE ROLE dcl_12237_grantor;
CREATE ROLE dcl_12237_member;
GRANT CREATE ON TABLESPACE dcl_12237_tablespace TO CURRENT_USER;
GRANT CREATE ON TABLESPACE dcl_12237_tablespace TO dcl_12237_grantor WITH GRANT OPTION;
SET ROLE dcl_12237_grantor;
REVOKE CREATE ON TABLESPACE dcl_12237_tablespace FROM CURRENT_USER GRANTED BY dcl_12237_grantor RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'schema_database_tablespace' AS privilege_scope;
DROP OWNED BY "dcl_12237_Grantee";
DROP OWNED BY dcl_12237_member;
DROP OWNED BY dcl_12237_grantor;
DROP ROLE IF EXISTS dcl_12237_member;
DROP ROLE IF EXISTS dcl_12237_grantor;
DROP ROLE IF EXISTS "dcl_12237_Grantee";
