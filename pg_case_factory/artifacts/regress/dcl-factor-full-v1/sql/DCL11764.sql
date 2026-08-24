-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_11 (parameter) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_11
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
-- factor grantee_shape=session_user
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=missing_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=effect_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_11764_grantor;
DROP ROLE IF EXISTS dcl_11764_member;
CREATE ROLE dcl_11764_grantor;
CREATE ROLE dcl_11764_member;
GRANT SELECT ON PARAMETER work_mem TO SESSION_USER;
GRANT SELECT ON PARAMETER work_mem TO dcl_11764_grantor WITH GRANT OPTION;
GRANT dcl_11764_grantor TO dcl_11764_member WITH SET TRUE;
SET ROLE dcl_11764_member;
SET ROLE dcl_11764_grantor;
REVOKE INHERIT OPTION FOR SELECT ON PARAMETER work_mem FROM SESSION_USER RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_11764_member;
DROP OWNED BY dcl_11764_grantor;
DROP ROLE IF EXISTS dcl_11764_member;
DROP ROLE IF EXISTS dcl_11764_grantor;
