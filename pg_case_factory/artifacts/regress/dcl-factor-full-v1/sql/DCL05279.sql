-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_12 (schema) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_12
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=current_role
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_05279_grantee;
DROP ROLE IF EXISTS dcl_05279_grantor;
DROP ROLE IF EXISTS dcl_05279_member;
CREATE ROLE dcl_05279_grantee;
CREATE ROLE dcl_05279_grantor;
CREATE ROLE dcl_05279_member;
DROP SCHEMA IF EXISTS dcl_05279_schema CASCADE;
CREATE SCHEMA dcl_05279_schema;
BEGIN;
SET ROLE dcl_05279_grantee;
GRANT USAGE ON SCHEMA dcl_05279_missing_object TO CURRENT_ROLE WITH GRANT OPTION GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT has_schema_privilege(CURRENT_USER, 'dcl_05279_schema', 'USAGE');
ROLLBACK;
DROP SCHEMA IF EXISTS dcl_05279_schema CASCADE;
DROP OWNED BY dcl_05279_grantee;
DROP OWNED BY dcl_05279_member;
DROP OWNED BY dcl_05279_grantor;
DROP ROLE IF EXISTS dcl_05279_member;
DROP ROLE IF EXISTS dcl_05279_grantor;
DROP ROLE IF EXISTS dcl_05279_grantee;
