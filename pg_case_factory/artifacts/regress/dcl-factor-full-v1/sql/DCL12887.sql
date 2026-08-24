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
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=role_name
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_12887_grantee;
DROP ROLE IF EXISTS dcl_12887_grantor;
DROP ROLE IF EXISTS dcl_12887_member;
CREATE ROLE dcl_12887_grantee;
CREATE ROLE dcl_12887_grantor;
CREATE ROLE dcl_12887_member;
DROP TYPE IF EXISTS dcl_12887_type;
CREATE TYPE dcl_12887_type AS ENUM ('alpha', 'beta');
GRANT USAGE ON TYPE dcl_12887_missing_object TO dcl_12887_grantee;
BEGIN;
SET ROLE dcl_12887_grantee;
REVOKE INHERIT OPTION FOR USAGE ON TYPE dcl_12887_missing_object FROM dcl_12887_grantee GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT has_type_privilege(CURRENT_USER, 'dcl_12887_type', 'USAGE');
ROLLBACK;
DROP TYPE IF EXISTS dcl_12887_type;
DROP OWNED BY dcl_12887_grantee;
DROP OWNED BY dcl_12887_member;
DROP OWNED BY dcl_12887_grantor;
DROP ROLE IF EXISTS dcl_12887_member;
DROP ROLE IF EXISTS dcl_12887_grantor;
DROP ROLE IF EXISTS dcl_12887_grantee;
