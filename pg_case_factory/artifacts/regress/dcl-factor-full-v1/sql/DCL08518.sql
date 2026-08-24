-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_4 (database) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_4
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=public
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
DROP ROLE IF EXISTS dcl_08518_grantor;
DROP ROLE IF EXISTS dcl_08518_member;
CREATE ROLE dcl_08518_grantor;
CREATE ROLE dcl_08518_member;
GRANT CONNECT ON DATABASE dcl_08518_missing_object TO PUBLIC;
GRANT CONNECT ON DATABASE dcl_08518_missing_object TO dcl_08518_grantor WITH GRANT OPTION;
GRANT dcl_08518_grantor TO dcl_08518_member WITH SET TRUE;
SET ROLE dcl_08518_member;
SET ROLE dcl_08518_grantor;
REVOKE INHERIT OPTION FOR CONNECT ON DATABASE dcl_08518_missing_object FROM PUBLIC RESTRICT;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_08518_member;
DROP OWNED BY dcl_08518_grantor;
DROP ROLE IF EXISTS dcl_08518_member;
DROP ROLE IF EXISTS dcl_08518_grantor;
