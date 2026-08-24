-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_13 (tablespace) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_13
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=role_name
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
DROP ROLE IF EXISTS dcl_12490_grantor;
DROP ROLE IF EXISTS dcl_12490_member;
CREATE ROLE dcl_12490_grantor;
CREATE ROLE dcl_12490_member;
GRANT CREATE ON TABLESPACE dcl_12490_missing_object TO dcl_12490_missing_role;
GRANT CREATE ON TABLESPACE dcl_12490_missing_object TO dcl_12490_grantor WITH GRANT OPTION;
GRANT dcl_12490_grantor TO dcl_12490_member WITH SET TRUE;
SET ROLE dcl_12490_member;
SET ROLE dcl_12490_grantor;
REVOKE GRANT OPTION FOR CREATE ON TABLESPACE dcl_12490_missing_object FROM dcl_12490_missing_role RESTRICT;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_12490_member;
DROP OWNED BY dcl_12490_grantor;
DROP ROLE IF EXISTS dcl_12490_member;
DROP ROLE IF EXISTS dcl_12490_grantor;
