-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_3 (sequence) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_3
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=session_user
-- factor grant_option_shape=admin_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=returned_rows
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_01317_Grantee";
DROP ROLE IF EXISTS dcl_01317_grantor;
DROP ROLE IF EXISTS dcl_01317_member;
CREATE ROLE "dcl_01317_Grantee";
CREATE ROLE dcl_01317_grantor;
CREATE ROLE dcl_01317_member;
DROP SEQUENCE IF EXISTS dcl_01317_sequence;
CREATE SEQUENCE dcl_01317_sequence;
SET ROLE "dcl_01317_Grantee";
GRANT USAGE ON SEQUENCE dcl_01317_missing_object TO SESSION_USER WITH ADMIN OPTION GRANTED BY dcl_01317_grantor;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'parameter_privilege' AS privilege_scope;
DROP SEQUENCE IF EXISTS dcl_01317_sequence;
DROP OWNED BY "dcl_01317_Grantee";
DROP OWNED BY dcl_01317_member;
DROP OWNED BY dcl_01317_grantor;
DROP ROLE IF EXISTS dcl_01317_member;
DROP ROLE IF EXISTS dcl_01317_grantor;
DROP ROLE IF EXISTS "dcl_01317_Grantee";
