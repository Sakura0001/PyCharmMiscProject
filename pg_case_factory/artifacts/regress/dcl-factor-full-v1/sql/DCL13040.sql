-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_14 (type) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=current_user
-- factor grant_option_shape=admin_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=plain_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=effect_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_13040_grantee;
DROP ROLE IF EXISTS dcl_13040_grantor;
DROP ROLE IF EXISTS dcl_13040_member;
CREATE ROLE dcl_13040_grantee;
CREATE ROLE dcl_13040_grantor;
CREATE ROLE dcl_13040_member;
DROP TYPE IF EXISTS dcl_13040_type;
CREATE TYPE dcl_13040_type AS ENUM ('alpha', 'beta');
GRANT USAGE ON TYPE dcl_13040_missing_object TO CURRENT_USER;
BEGIN;
SET ROLE dcl_13040_grantee;
REVOKE ADMIN OPTION FOR USAGE ON TYPE dcl_13040_missing_object FROM CURRENT_USER GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP TYPE IF EXISTS dcl_13040_type;
DROP OWNED BY dcl_13040_grantee;
DROP OWNED BY dcl_13040_member;
DROP OWNED BY dcl_13040_grantor;
DROP ROLE IF EXISTS dcl_13040_member;
DROP ROLE IF EXISTS dcl_13040_grantor;
DROP ROLE IF EXISTS dcl_13040_grantee;
