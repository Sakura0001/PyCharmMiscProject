-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_14 (type) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
-- factor grantee_shape=current_role
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
DROP ROLE IF EXISTS dcl_06304_grantor;
DROP ROLE IF EXISTS dcl_06304_member;
CREATE ROLE dcl_06304_grantor;
CREATE ROLE dcl_06304_member;
DROP TYPE IF EXISTS dcl_06304_type;
CREATE TYPE dcl_06304_type AS ENUM ('alpha', 'beta');
GRANT USAGE ON TYPE dcl_06304_missing_object TO dcl_06304_grantor WITH GRANT OPTION;
GRANT dcl_06304_grantor TO dcl_06304_member WITH SET TRUE;
SET ROLE dcl_06304_member;
SET ROLE dcl_06304_grantor;
GRANT USAGE ON TYPE dcl_06304_missing_object TO CURRENT_ROLE WITH INHERIT TRUE;
RESET ROLE;
SELECT true AS privilege_effect_observed;
RESET ROLE;
RESET ALL;
DROP TYPE IF EXISTS dcl_06304_type;
DROP OWNED BY dcl_06304_member;
DROP OWNED BY dcl_06304_grantor;
DROP ROLE IF EXISTS dcl_06304_member;
DROP ROLE IF EXISTS dcl_06304_grantor;
