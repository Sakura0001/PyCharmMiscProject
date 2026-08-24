-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_14 (type) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
-- factor expected_status=success
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=current_role
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=none
-- factor ownership_boundary=owner
-- factor verification_mode=effect_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_12680_grantee;
DROP ROLE IF EXISTS dcl_12680_grantor;
DROP ROLE IF EXISTS dcl_12680_member;
CREATE ROLE dcl_12680_grantee;
CREATE ROLE dcl_12680_grantor;
CREATE ROLE dcl_12680_member;
DROP TYPE IF EXISTS dcl_12680_type;
CREATE TYPE dcl_12680_type AS ENUM ('alpha', 'beta');
GRANT USAGE ON TYPE dcl_12680_type TO CURRENT_ROLE;
BEGIN;
REVOKE USAGE ON TYPE dcl_12680_type FROM CURRENT_ROLE GRANTED BY CURRENT_USER RESTRICT;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP TYPE IF EXISTS dcl_12680_type;
DROP OWNED BY dcl_12680_grantee;
DROP OWNED BY dcl_12680_member;
DROP OWNED BY dcl_12680_grantor;
DROP ROLE IF EXISTS dcl_12680_member;
DROP ROLE IF EXISTS dcl_12680_grantor;
DROP ROLE IF EXISTS dcl_12680_grantee;
