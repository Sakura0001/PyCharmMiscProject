-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_11 (parameter) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_11
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=public
-- factor grant_option_shape=grant_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=missing_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=error_assertion
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_11602_grantor;
DROP ROLE IF EXISTS dcl_11602_member;
CREATE ROLE dcl_11602_grantor;
CREATE ROLE dcl_11602_member;
GRANT SELECT ON PARAMETER work_mem TO PUBLIC;
GRANT SELECT ON PARAMETER work_mem TO dcl_11602_grantor WITH GRANT OPTION;
GRANT dcl_11602_grantor TO dcl_11602_member WITH SET TRUE;
SET ROLE dcl_11602_member;
SET ROLE dcl_11602_grantor;
REVOKE GRANT OPTION FOR SELECT ON PARAMETER work_mem FROM PUBLIC RESTRICT;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_11602_member;
DROP OWNED BY dcl_11602_grantor;
DROP ROLE IF EXISTS dcl_11602_member;
DROP ROLE IF EXISTS dcl_11602_grantor;
