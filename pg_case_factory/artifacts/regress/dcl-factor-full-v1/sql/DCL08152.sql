-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_3 (sequence) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_3
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
-- factor grantee_shape=current_user
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
DROP ROLE IF EXISTS dcl_08152_grantor;
DROP ROLE IF EXISTS dcl_08152_member;
CREATE ROLE dcl_08152_grantor;
CREATE ROLE dcl_08152_member;
DROP SEQUENCE IF EXISTS dcl_08152_sequence;
CREATE SEQUENCE dcl_08152_sequence;
GRANT USAGE ON SEQUENCE dcl_08152_missing_object TO CURRENT_USER;
GRANT USAGE ON SEQUENCE dcl_08152_missing_object TO dcl_08152_grantor WITH GRANT OPTION;
GRANT dcl_08152_grantor TO dcl_08152_member WITH SET TRUE;
SET ROLE dcl_08152_member;
SET ROLE dcl_08152_grantor;
REVOKE INHERIT OPTION FOR USAGE ON SEQUENCE dcl_08152_missing_object FROM CURRENT_USER RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
RESET ROLE;
RESET ALL;
DROP SEQUENCE IF EXISTS dcl_08152_sequence;
DROP OWNED BY dcl_08152_member;
DROP OWNED BY dcl_08152_grantor;
DROP ROLE IF EXISTS dcl_08152_member;
DROP ROLE IF EXISTS dcl_08152_grantor;
