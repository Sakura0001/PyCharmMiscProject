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
-- factor grantee_shape=role_name
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
DROP ROLE IF EXISTS dcl_01330_grantor;
DROP ROLE IF EXISTS dcl_01330_member;
CREATE ROLE dcl_01330_grantor;
CREATE ROLE dcl_01330_member;
DROP SEQUENCE IF EXISTS dcl_01330_sequence;
CREATE SEQUENCE dcl_01330_sequence;
GRANT USAGE ON SEQUENCE dcl_01330_missing_object TO dcl_01330_grantor WITH GRANT OPTION;
GRANT dcl_01330_grantor TO dcl_01330_member WITH SET TRUE;
SET ROLE dcl_01330_member;
SET ROLE dcl_01330_grantor;
GRANT USAGE ON SEQUENCE dcl_01330_missing_object TO dcl_01330_missing_role WITH INHERIT TRUE;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
RESET ROLE;
RESET ALL;
DROP SEQUENCE IF EXISTS dcl_01330_sequence;
DROP OWNED BY dcl_01330_member;
DROP OWNED BY dcl_01330_grantor;
DROP ROLE IF EXISTS dcl_01330_member;
DROP ROLE IF EXISTS dcl_01330_grantor;
