-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_12 (schema) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_12
-- factor expected_status=success
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=session_user
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
DROP ROLE IF EXISTS "dcl_11795_Grantee";
DROP ROLE IF EXISTS dcl_11795_grantor;
DROP ROLE IF EXISTS dcl_11795_member;
CREATE ROLE "dcl_11795_Grantee";
CREATE ROLE dcl_11795_grantor;
CREATE ROLE dcl_11795_member;
DROP SCHEMA IF EXISTS dcl_11795_schema CASCADE;
CREATE SCHEMA dcl_11795_schema;
GRANT USAGE ON SCHEMA dcl_11795_schema TO SESSION_USER;
GRANT USAGE ON SCHEMA dcl_11795_schema TO dcl_11795_grantor WITH GRANT OPTION;
BEGIN;
SET ROLE dcl_11795_grantor;
REVOKE GRANT OPTION FOR USAGE ON SCHEMA dcl_11795_schema FROM SESSION_USER GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP SCHEMA IF EXISTS dcl_11795_schema CASCADE;
DROP OWNED BY "dcl_11795_Grantee";
DROP OWNED BY dcl_11795_member;
DROP OWNED BY dcl_11795_grantor;
DROP ROLE IF EXISTS dcl_11795_member;
DROP ROLE IF EXISTS dcl_11795_grantor;
DROP ROLE IF EXISTS "dcl_11795_Grantee";
