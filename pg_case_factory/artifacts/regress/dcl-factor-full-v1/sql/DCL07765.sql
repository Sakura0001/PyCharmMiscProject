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
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=public
-- factor grant_option_shape=admin_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=missing_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=returned_rows
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_07765_grantor;
DROP ROLE IF EXISTS dcl_07765_member;
CREATE ROLE dcl_07765_grantor;
CREATE ROLE dcl_07765_member;
DROP SEQUENCE IF EXISTS dcl_07765_sequence;
CREATE SEQUENCE dcl_07765_sequence;
GRANT USAGE ON SEQUENCE dcl_07765_missing_object TO PUBLIC;
GRANT USAGE ON SEQUENCE dcl_07765_missing_object TO dcl_07765_grantor WITH GRANT OPTION;
GRANT dcl_07765_grantor TO dcl_07765_member WITH SET TRUE;
SET ROLE dcl_07765_member;
SET ROLE dcl_07765_grantor;
REVOKE ADMIN OPTION FOR USAGE ON SEQUENCE dcl_07765_missing_object FROM PUBLIC RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'table_privilege' AS privilege_scope;
RESET ROLE;
RESET ALL;
DROP SEQUENCE IF EXISTS dcl_07765_sequence;
DROP OWNED BY dcl_07765_member;
DROP OWNED BY dcl_07765_grantor;
DROP ROLE IF EXISTS dcl_07765_member;
DROP ROLE IF EXISTS dcl_07765_grantor;
