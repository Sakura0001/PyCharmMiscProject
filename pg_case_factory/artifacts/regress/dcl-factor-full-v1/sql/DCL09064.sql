-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_5 (domain) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_5
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
DROP ROLE IF EXISTS dcl_09064_grantor;
DROP ROLE IF EXISTS dcl_09064_member;
CREATE ROLE dcl_09064_grantor;
CREATE ROLE dcl_09064_member;
DROP DOMAIN IF EXISTS dcl_09064_domain;
CREATE DOMAIN dcl_09064_domain AS text;
GRANT USAGE ON DOMAIN dcl_09064_missing_object TO SESSION_USER;
GRANT USAGE ON DOMAIN dcl_09064_missing_object TO dcl_09064_grantor WITH GRANT OPTION;
GRANT dcl_09064_grantor TO dcl_09064_member WITH SET TRUE;
SET ROLE dcl_09064_member;
SET ROLE dcl_09064_grantor;
REVOKE INHERIT OPTION FOR USAGE ON DOMAIN dcl_09064_missing_object FROM SESSION_USER RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
RESET ROLE;
RESET ALL;
DROP DOMAIN IF EXISTS dcl_09064_domain;
DROP OWNED BY dcl_09064_member;
DROP OWNED BY dcl_09064_grantor;
DROP ROLE IF EXISTS dcl_09064_member;
DROP ROLE IF EXISTS dcl_09064_grantor;
