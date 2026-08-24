-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_14 (type) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
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
DROP ROLE IF EXISTS dcl_06004_grantor;
DROP ROLE IF EXISTS dcl_06004_member;
CREATE ROLE dcl_06004_grantor;
CREATE ROLE dcl_06004_member;
DROP TYPE IF EXISTS dcl_06004_type;
CREATE TYPE dcl_06004_type AS ENUM ('alpha', 'beta');
GRANT USAGE ON TYPE dcl_06004_missing_object TO dcl_06004_grantor WITH GRANT OPTION;
GRANT dcl_06004_grantor TO dcl_06004_member WITH SET TRUE;
SET ROLE dcl_06004_member;
SET ROLE dcl_06004_grantor;
GRANT USAGE ON TYPE dcl_06004_missing_object TO CURRENT_ROLE WITH INHERIT TRUE;
RESET ROLE;
SELECT true AS privilege_effect_observed;
RESET ROLE;
RESET ALL;
DROP TYPE IF EXISTS dcl_06004_type;
DROP OWNED BY dcl_06004_member;
DROP OWNED BY dcl_06004_grantor;
DROP ROLE IF EXISTS dcl_06004_member;
DROP ROLE IF EXISTS dcl_06004_grantor;
