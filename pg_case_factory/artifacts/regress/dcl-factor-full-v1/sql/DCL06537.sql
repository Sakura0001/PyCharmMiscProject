-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_15 (role_membership) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_15
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=session_user
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=returned_rows
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_06537_Grantee";
DROP ROLE IF EXISTS dcl_06537_grantor;
DROP ROLE IF EXISTS dcl_06537_member;
CREATE ROLE "dcl_06537_Grantee";
CREATE ROLE dcl_06537_grantor;
CREATE ROLE dcl_06537_member;
SET ROLE "dcl_06537_Grantee";
GRANT dcl_06537_missing_member TO SESSION_USER GRANTED BY dcl_06537_grantor;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'schema_database_tablespace' AS privilege_scope;
DROP OWNED BY "dcl_06537_Grantee";
DROP OWNED BY dcl_06537_member;
DROP OWNED BY dcl_06537_grantor;
DROP ROLE IF EXISTS dcl_06537_member;
DROP ROLE IF EXISTS dcl_06537_grantor;
DROP ROLE IF EXISTS "dcl_06537_Grantee";
