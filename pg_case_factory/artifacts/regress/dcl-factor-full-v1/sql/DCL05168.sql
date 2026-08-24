-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_12 (schema) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_12
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=current_user
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
DROP ROLE IF EXISTS dcl_05168_grantee;
DROP ROLE IF EXISTS dcl_05168_grantor;
DROP ROLE IF EXISTS dcl_05168_member;
CREATE ROLE dcl_05168_grantee;
CREATE ROLE dcl_05168_grantor;
CREATE ROLE dcl_05168_member;
DROP SCHEMA IF EXISTS dcl_05168_schema CASCADE;
CREATE SCHEMA dcl_05168_schema;
BEGIN;
SET ROLE dcl_05168_grantee;
GRANT USAGE ON SCHEMA dcl_05168_missing_object TO CURRENT_USER GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP SCHEMA IF EXISTS dcl_05168_schema CASCADE;
DROP OWNED BY dcl_05168_grantee;
DROP OWNED BY dcl_05168_member;
DROP OWNED BY dcl_05168_grantor;
DROP ROLE IF EXISTS dcl_05168_member;
DROP ROLE IF EXISTS dcl_05168_grantor;
DROP ROLE IF EXISTS dcl_05168_grantee;
