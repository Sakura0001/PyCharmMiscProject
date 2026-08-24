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
-- factor grantee_shape=role_name
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
DROP ROLE IF EXISTS dcl_12668_grantee;
DROP ROLE IF EXISTS dcl_12668_grantor;
DROP ROLE IF EXISTS dcl_12668_member;
CREATE ROLE dcl_12668_grantee;
CREATE ROLE dcl_12668_grantor;
CREATE ROLE dcl_12668_member;
DROP TYPE IF EXISTS dcl_12668_type;
CREATE TYPE dcl_12668_type AS ENUM ('alpha', 'beta');
GRANT USAGE ON TYPE dcl_12668_type TO dcl_12668_grantee;
BEGIN;
REVOKE USAGE ON TYPE dcl_12668_type FROM dcl_12668_grantee GRANTED BY CURRENT_USER RESTRICT;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP TYPE IF EXISTS dcl_12668_type;
DROP OWNED BY dcl_12668_grantee;
DROP OWNED BY dcl_12668_member;
DROP OWNED BY dcl_12668_grantor;
DROP ROLE IF EXISTS dcl_12668_member;
DROP ROLE IF EXISTS dcl_12668_grantor;
DROP ROLE IF EXISTS dcl_12668_grantee;
