-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_3 (sequence) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_3
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=current_role
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
DROP ROLE IF EXISTS "dcl_07953_Grantee";
DROP ROLE IF EXISTS dcl_07953_grantor;
DROP ROLE IF EXISTS dcl_07953_member;
CREATE ROLE "dcl_07953_Grantee";
CREATE ROLE dcl_07953_grantor;
CREATE ROLE dcl_07953_member;
DROP SEQUENCE IF EXISTS dcl_07953_sequence;
CREATE SEQUENCE dcl_07953_sequence;
GRANT USAGE ON SEQUENCE dcl_07953_missing_object TO CURRENT_ROLE;
SET ROLE "dcl_07953_Grantee";
REVOKE USAGE ON SEQUENCE dcl_07953_missing_object FROM CURRENT_ROLE GRANTED BY dcl_07953_grantor RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'routine_language_type_fdw_server' AS privilege_scope;
DROP SEQUENCE IF EXISTS dcl_07953_sequence;
DROP OWNED BY "dcl_07953_Grantee";
DROP OWNED BY dcl_07953_member;
DROP OWNED BY dcl_07953_grantor;
DROP ROLE IF EXISTS dcl_07953_member;
DROP ROLE IF EXISTS dcl_07953_grantor;
DROP ROLE IF EXISTS "dcl_07953_Grantee";
