-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_7 (foreign_server) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_7
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=session_user
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=plain_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=effect_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_09716_grantee;
DROP ROLE IF EXISTS dcl_09716_grantor;
DROP ROLE IF EXISTS dcl_09716_member;
CREATE ROLE dcl_09716_grantee;
CREATE ROLE dcl_09716_grantor;
CREATE ROLE dcl_09716_member;
DROP SERVER IF EXISTS dcl_09716_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09716_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_09716_fdw;
CREATE SERVER dcl_09716_server FOREIGN DATA WRAPPER dcl_09716_fdw;
GRANT USAGE ON FOREIGN SERVER dcl_09716_missing_object TO SESSION_USER;
BEGIN;
SET ROLE dcl_09716_grantee;
REVOKE USAGE ON FOREIGN SERVER dcl_09716_missing_object FROM SESSION_USER GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP SERVER IF EXISTS dcl_09716_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09716_fdw CASCADE;
DROP OWNED BY dcl_09716_grantee;
DROP OWNED BY dcl_09716_member;
DROP OWNED BY dcl_09716_grantor;
DROP ROLE IF EXISTS dcl_09716_member;
DROP ROLE IF EXISTS dcl_09716_grantor;
DROP ROLE IF EXISTS dcl_09716_grantee;
