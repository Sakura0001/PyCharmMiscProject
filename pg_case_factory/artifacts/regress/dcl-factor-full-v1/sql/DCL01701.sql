-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_4 (database) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_4
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
DROP ROLE IF EXISTS "dcl_01701_Grantee";
DROP ROLE IF EXISTS dcl_01701_grantor;
DROP ROLE IF EXISTS dcl_01701_member;
CREATE ROLE "dcl_01701_Grantee";
CREATE ROLE dcl_01701_grantor;
CREATE ROLE dcl_01701_member;
SET ROLE "dcl_01701_Grantee";
GRANT CONNECT ON DATABASE dcl_01701_missing_object TO SESSION_USER GRANTED BY dcl_01701_grantor;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'role_membership' AS privilege_scope;
DROP OWNED BY "dcl_01701_Grantee";
DROP OWNED BY dcl_01701_member;
DROP OWNED BY dcl_01701_grantor;
DROP ROLE IF EXISTS dcl_01701_member;
DROP ROLE IF EXISTS dcl_01701_grantor;
DROP ROLE IF EXISTS "dcl_01701_Grantee";
