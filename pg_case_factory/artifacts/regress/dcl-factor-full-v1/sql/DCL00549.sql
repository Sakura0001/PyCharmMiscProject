-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_2 (column) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=current_user
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
DROP TABLE IF EXISTS dcl_00549_table;
DROP ROLE IF EXISTS "dcl_00549_Grantee";
DROP ROLE IF EXISTS dcl_00549_grantor;
DROP ROLE IF EXISTS dcl_00549_member;
CREATE ROLE "dcl_00549_Grantee";
CREATE ROLE dcl_00549_grantor;
CREATE ROLE dcl_00549_member;
CREATE TABLE dcl_00549_table (id integer, payload text);
SET ROLE "dcl_00549_Grantee";
GRANT EXECUTE (payload) ON TABLE dcl_00549_missing_object TO CURRENT_USER GRANTED BY dcl_00549_grantor;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'table_privilege' AS privilege_scope;
DROP OWNED BY "dcl_00549_Grantee";
DROP OWNED BY dcl_00549_member;
DROP OWNED BY dcl_00549_grantor;
DROP ROLE IF EXISTS dcl_00549_member;
DROP ROLE IF EXISTS dcl_00549_grantor;
DROP ROLE IF EXISTS "dcl_00549_Grantee";
DROP TABLE IF EXISTS dcl_00549_table;
