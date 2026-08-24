-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_4 (database) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_4
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
-- factor grantee_shape=role_name
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
DROP ROLE IF EXISTS "dcl_01773_Grantee";
DROP ROLE IF EXISTS dcl_01773_grantor;
DROP ROLE IF EXISTS dcl_01773_member;
CREATE ROLE "dcl_01773_Grantee";
CREATE ROLE dcl_01773_grantor;
CREATE ROLE dcl_01773_member;
SET ROLE "dcl_01773_Grantee";
GRANT CONNECT ON DATABASE dcl_01773_missing_object TO "dcl_01773_Grantee" GRANTED BY dcl_01773_grantor;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'table_maintain' AS privilege_scope;
DROP OWNED BY "dcl_01773_Grantee";
DROP OWNED BY dcl_01773_member;
DROP OWNED BY dcl_01773_grantor;
DROP ROLE IF EXISTS dcl_01773_member;
DROP ROLE IF EXISTS dcl_01773_grantor;
DROP ROLE IF EXISTS "dcl_01773_Grantee";
