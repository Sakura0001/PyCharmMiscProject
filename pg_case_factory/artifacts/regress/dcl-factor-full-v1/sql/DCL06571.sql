-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_15 (role_membership) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_15
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=current_role
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
DROP ROLE IF EXISTS dcl_06571_grantor;
DROP ROLE IF EXISTS dcl_06571_member;
CREATE ROLE dcl_06571_grantor;
CREATE ROLE dcl_06571_member;
GRANT dcl_06571_missing_member TO dcl_06571_grantor WITH GRANT OPTION;
GRANT dcl_06571_grantor TO dcl_06571_member WITH SET TRUE;
SET ROLE dcl_06571_member;
SET ROLE dcl_06571_grantor;
GRANT dcl_06571_missing_member TO CURRENT_ROLE;
RESET ROLE;
SELECT true AS role_membership_statement_completed;
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_06571_member;
DROP OWNED BY dcl_06571_grantor;
DROP ROLE IF EXISTS dcl_06571_member;
DROP ROLE IF EXISTS dcl_06571_grantor;
