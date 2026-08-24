-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_15 (role_membership) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_15
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
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
DROP ROLE IF EXISTS dcl_13306_grantor;
DROP ROLE IF EXISTS dcl_13306_member;
CREATE ROLE dcl_13306_grantor;
CREATE ROLE dcl_13306_member;
GRANT dcl_13306_missing_member TO dcl_13306_grantor WITH GRANT OPTION;
GRANT dcl_13306_grantor TO dcl_13306_member WITH SET TRUE;
SET ROLE dcl_13306_member;
SET ROLE dcl_13306_grantor;
REVOKE SET OPTION FOR dcl_13306_missing_member FROM CURRENT_ROLE RESTRICT;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_13306_member;
DROP OWNED BY dcl_13306_grantor;
DROP ROLE IF EXISTS dcl_13306_member;
DROP ROLE IF EXISTS dcl_13306_grantor;
