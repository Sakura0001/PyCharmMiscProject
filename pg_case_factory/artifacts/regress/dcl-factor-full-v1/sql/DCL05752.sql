-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_13 (tablespace) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_13
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=session_user
-- factor grant_option_shape=grant_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=missing_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=effect_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_05752_grantor;
DROP ROLE IF EXISTS dcl_05752_member;
CREATE ROLE dcl_05752_grantor;
CREATE ROLE dcl_05752_member;
GRANT CREATE ON TABLESPACE dcl_05752_missing_object TO dcl_05752_grantor WITH GRANT OPTION;
GRANT dcl_05752_grantor TO dcl_05752_member WITH SET TRUE;
SET ROLE dcl_05752_member;
SET ROLE dcl_05752_grantor;
GRANT CREATE ON TABLESPACE dcl_05752_missing_object TO SESSION_USER WITH GRANT OPTION;
RESET ROLE;
SELECT true AS privilege_effect_observed;
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_05752_member;
DROP OWNED BY dcl_05752_grantor;
DROP ROLE IF EXISTS dcl_05752_member;
DROP ROLE IF EXISTS dcl_05752_grantor;
