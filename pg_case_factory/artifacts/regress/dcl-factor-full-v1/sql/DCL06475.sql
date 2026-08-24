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
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=missing_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_06475_grantor;
DROP ROLE IF EXISTS dcl_06475_member;
CREATE ROLE dcl_06475_grantor;
CREATE ROLE dcl_06475_member;
GRANT dcl_06475_missing_member TO dcl_06475_grantor WITH GRANT OPTION;
GRANT dcl_06475_grantor TO dcl_06475_member WITH SET TRUE;
SET ROLE dcl_06475_member;
SET ROLE dcl_06475_grantor;
GRANT dcl_06475_missing_member TO SESSION_USER;
RESET ROLE;
SELECT true AS role_membership_statement_completed;
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_06475_member;
DROP OWNED BY dcl_06475_grantor;
DROP ROLE IF EXISTS dcl_06475_member;
DROP ROLE IF EXISTS dcl_06475_grantor;
