-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_15 (role_membership) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_15
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
-- factor grantee_shape=session_user
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
DROP ROLE IF EXISTS dcl_06478_grantor;
DROP ROLE IF EXISTS dcl_06478_member;
CREATE ROLE dcl_06478_grantor;
CREATE ROLE dcl_06478_member;
GRANT dcl_06478_missing_member TO dcl_06478_grantor WITH GRANT OPTION;
GRANT dcl_06478_grantor TO dcl_06478_member WITH SET TRUE;
SET ROLE dcl_06478_member;
SET ROLE dcl_06478_grantor;
GRANT dcl_06478_missing_member TO SESSION_USER WITH GRANT OPTION;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_06478_member;
DROP OWNED BY dcl_06478_grantor;
DROP ROLE IF EXISTS dcl_06478_member;
DROP ROLE IF EXISTS dcl_06478_grantor;
