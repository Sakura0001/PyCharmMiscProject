-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_9 (language) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_9
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=current_role
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
DROP ROLE IF EXISTS dcl_10654_grantor;
DROP ROLE IF EXISTS dcl_10654_member;
CREATE ROLE dcl_10654_grantor;
CREATE ROLE dcl_10654_member;
GRANT USAGE ON LANGUAGE plpgsql TO CURRENT_ROLE;
GRANT USAGE ON LANGUAGE plpgsql TO dcl_10654_grantor WITH GRANT OPTION;
GRANT dcl_10654_grantor TO dcl_10654_member WITH SET TRUE;
SET ROLE dcl_10654_member;
SET ROLE dcl_10654_grantor;
REVOKE GRANT OPTION FOR USAGE ON LANGUAGE plpgsql FROM CURRENT_ROLE RESTRICT;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_10654_member;
DROP OWNED BY dcl_10654_grantor;
DROP ROLE IF EXISTS dcl_10654_member;
DROP ROLE IF EXISTS dcl_10654_grantor;
