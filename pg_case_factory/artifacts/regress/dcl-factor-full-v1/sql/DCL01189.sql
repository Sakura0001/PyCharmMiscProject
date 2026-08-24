-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_3 (sequence) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_3
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=session_user
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=missing_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=returned_rows
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_01189_grantor;
DROP ROLE IF EXISTS dcl_01189_member;
CREATE ROLE dcl_01189_grantor;
CREATE ROLE dcl_01189_member;
DROP SEQUENCE IF EXISTS dcl_01189_sequence;
CREATE SEQUENCE dcl_01189_sequence;
GRANT USAGE ON SEQUENCE dcl_01189_missing_object TO dcl_01189_grantor WITH GRANT OPTION;
GRANT dcl_01189_grantor TO dcl_01189_member WITH SET TRUE;
SET ROLE dcl_01189_member;
SET ROLE dcl_01189_grantor;
GRANT USAGE ON SEQUENCE dcl_01189_missing_object TO SESSION_USER;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'routine_language_type_fdw_server' AS privilege_scope;
RESET ROLE;
RESET ALL;
DROP SEQUENCE IF EXISTS dcl_01189_sequence;
DROP OWNED BY dcl_01189_member;
DROP OWNED BY dcl_01189_grantor;
DROP ROLE IF EXISTS dcl_01189_member;
DROP ROLE IF EXISTS dcl_01189_grantor;
