-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_3 (sequence) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_3
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
-- factor grantee_shape=current_role
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=missing_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=error_assertion
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_01354_grantor;
DROP ROLE IF EXISTS dcl_01354_member;
CREATE ROLE dcl_01354_grantor;
CREATE ROLE dcl_01354_member;
DROP SEQUENCE IF EXISTS dcl_01354_sequence;
CREATE SEQUENCE dcl_01354_sequence;
GRANT USAGE ON SEQUENCE dcl_01354_missing_object TO dcl_01354_grantor WITH GRANT OPTION;
GRANT dcl_01354_grantor TO dcl_01354_member WITH SET TRUE;
SET ROLE dcl_01354_member;
SET ROLE dcl_01354_grantor;
GRANT USAGE ON SEQUENCE dcl_01354_missing_object TO CURRENT_ROLE WITH INHERIT TRUE;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
RESET ROLE;
RESET ALL;
DROP SEQUENCE IF EXISTS dcl_01354_sequence;
DROP OWNED BY dcl_01354_member;
DROP OWNED BY dcl_01354_grantor;
DROP ROLE IF EXISTS dcl_01354_member;
DROP ROLE IF EXISTS dcl_01354_grantor;
