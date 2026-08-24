-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_6 (foreign_data_wrapper) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_6
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=session_user
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
DROP ROLE IF EXISTS dcl_09335_grantee;
DROP ROLE IF EXISTS dcl_09335_grantor;
DROP ROLE IF EXISTS dcl_09335_member;
CREATE ROLE dcl_09335_grantee;
CREATE ROLE dcl_09335_grantor;
CREATE ROLE dcl_09335_member;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09335_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_09335_fdw;
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_09335_missing_object TO SESSION_USER;
BEGIN;
SET ROLE dcl_09335_grantee;
REVOKE INHERIT OPTION FOR USAGE ON FOREIGN DATA WRAPPER dcl_09335_missing_object FROM SESSION_USER GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT true AS fdw_privilege_statement_completed;
ROLLBACK;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09335_fdw CASCADE;
DROP OWNED BY dcl_09335_grantee;
DROP OWNED BY dcl_09335_member;
DROP OWNED BY dcl_09335_grantor;
DROP ROLE IF EXISTS dcl_09335_member;
DROP ROLE IF EXISTS dcl_09335_grantor;
DROP ROLE IF EXISTS dcl_09335_grantee;
