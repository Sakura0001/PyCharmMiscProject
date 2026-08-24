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
-- factor grantee_shape=current_user
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=plain_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=error_assertion
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_01178_grantee;
DROP ROLE IF EXISTS dcl_01178_grantor;
DROP ROLE IF EXISTS dcl_01178_member;
CREATE ROLE dcl_01178_grantee;
CREATE ROLE dcl_01178_grantor;
CREATE ROLE dcl_01178_member;
DROP SEQUENCE IF EXISTS dcl_01178_sequence;
CREATE SEQUENCE dcl_01178_sequence;
BEGIN;
SET ROLE dcl_01178_grantee;
GRANT USAGE ON SEQUENCE dcl_01178_missing_object TO CURRENT_USER GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
ROLLBACK;
DROP SEQUENCE IF EXISTS dcl_01178_sequence;
DROP OWNED BY dcl_01178_grantee;
DROP OWNED BY dcl_01178_member;
DROP OWNED BY dcl_01178_grantor;
DROP ROLE IF EXISTS dcl_01178_member;
DROP ROLE IF EXISTS dcl_01178_grantor;
DROP ROLE IF EXISTS dcl_01178_grantee;
