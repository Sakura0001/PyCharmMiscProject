-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_3 (sequence) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_3
-- factor expected_status=success
-- factor privilege_scope=table_privilege
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
DROP ROLE IF EXISTS dcl_07746_grantee;
DROP ROLE IF EXISTS dcl_07746_grantor;
DROP ROLE IF EXISTS dcl_07746_member;
CREATE ROLE dcl_07746_grantee;
CREATE ROLE dcl_07746_grantor;
CREATE ROLE dcl_07746_member;
DROP SEQUENCE IF EXISTS dcl_07746_sequence;
CREATE SEQUENCE dcl_07746_sequence;
GRANT USAGE ON SEQUENCE dcl_07746_sequence TO SESSION_USER;
REVOKE GRANT OPTION FOR USAGE ON SEQUENCE dcl_07746_sequence FROM SESSION_USER GRANTED BY dcl_07746_grantor RESTRICT;
SELECT 'revoke' AS completed_statement, 'table_privilege' AS privilege_scope;
DROP SEQUENCE IF EXISTS dcl_07746_sequence;
DROP OWNED BY dcl_07746_grantee;
DROP OWNED BY dcl_07746_member;
DROP OWNED BY dcl_07746_grantor;
DROP ROLE IF EXISTS dcl_07746_member;
DROP ROLE IF EXISTS dcl_07746_grantor;
DROP ROLE IF EXISTS dcl_07746_grantee;
