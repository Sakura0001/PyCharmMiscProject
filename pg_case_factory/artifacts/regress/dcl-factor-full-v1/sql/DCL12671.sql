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
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=member_role
-- factor verification_mode=effect_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS "dcl_12671_Grantee";
DROP ROLE IF EXISTS dcl_12671_grantor;
DROP ROLE IF EXISTS dcl_12671_member;
CREATE ROLE "dcl_12671_Grantee";
CREATE ROLE dcl_12671_grantor;
CREATE ROLE dcl_12671_member;
DROP TYPE IF EXISTS dcl_12671_type;
CREATE TYPE dcl_12671_type AS ENUM ('alpha', 'beta');
GRANT USAGE ON TYPE dcl_12671_type TO "dcl_12671_Grantee";
GRANT USAGE ON TYPE dcl_12671_type TO dcl_12671_grantor WITH GRANT OPTION;
BEGIN;
SET ROLE dcl_12671_grantor;
REVOKE GRANT OPTION FOR USAGE ON TYPE dcl_12671_type FROM "dcl_12671_Grantee" GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP TYPE IF EXISTS dcl_12671_type;
DROP OWNED BY "dcl_12671_Grantee";
DROP OWNED BY dcl_12671_member;
DROP OWNED BY dcl_12671_grantor;
DROP ROLE IF EXISTS dcl_12671_member;
DROP ROLE IF EXISTS dcl_12671_grantor;
DROP ROLE IF EXISTS "dcl_12671_Grantee";
