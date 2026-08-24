-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_2 (column) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=failure
-- factor privilege_scope=role_membership
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
DROP TABLE IF EXISTS dcl_00801_table;
DROP ROLE IF EXISTS "dcl_00801_Grantee";
DROP ROLE IF EXISTS dcl_00801_grantor;
DROP ROLE IF EXISTS dcl_00801_member;
CREATE ROLE "dcl_00801_Grantee";
CREATE ROLE dcl_00801_grantor;
CREATE ROLE dcl_00801_member;
CREATE TABLE dcl_00801_table (id integer, payload text);
SET ROLE "dcl_00801_Grantee";
GRANT EXECUTE (payload) ON TABLE dcl_00801_missing_object TO SESSION_USER GRANTED BY dcl_00801_grantor;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'role_membership' AS privilege_scope;
DROP OWNED BY "dcl_00801_Grantee";
DROP OWNED BY dcl_00801_member;
DROP OWNED BY dcl_00801_grantor;
DROP ROLE IF EXISTS dcl_00801_member;
DROP ROLE IF EXISTS dcl_00801_grantor;
DROP ROLE IF EXISTS "dcl_00801_Grantee";
DROP TABLE IF EXISTS dcl_00801_table;
