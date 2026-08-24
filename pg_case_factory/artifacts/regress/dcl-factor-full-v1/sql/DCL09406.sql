-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_6 (foreign_data_wrapper) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_6
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
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
DROP ROLE IF EXISTS dcl_09406_grantor;
DROP ROLE IF EXISTS dcl_09406_member;
CREATE ROLE dcl_09406_grantor;
CREATE ROLE dcl_09406_member;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09406_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_09406_fdw;
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_09406_missing_object TO dcl_09406_missing_role;
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_09406_missing_object TO dcl_09406_grantor WITH GRANT OPTION;
GRANT dcl_09406_grantor TO dcl_09406_member WITH SET TRUE;
SET ROLE dcl_09406_member;
SET ROLE dcl_09406_grantor;
REVOKE INHERIT OPTION FOR USAGE ON FOREIGN DATA WRAPPER dcl_09406_missing_object FROM dcl_09406_missing_role RESTRICT;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
RESET ROLE;
RESET ALL;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09406_fdw CASCADE;
DROP OWNED BY dcl_09406_member;
DROP OWNED BY dcl_09406_grantor;
DROP ROLE IF EXISTS dcl_09406_member;
DROP ROLE IF EXISTS dcl_09406_grantor;
