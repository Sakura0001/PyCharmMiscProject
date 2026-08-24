-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_6 (foreign_data_wrapper) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_6
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=current_user
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
DROP ROLE IF EXISTS dcl_09263_grantee;
DROP ROLE IF EXISTS dcl_09263_grantor;
DROP ROLE IF EXISTS dcl_09263_member;
CREATE ROLE dcl_09263_grantee;
CREATE ROLE dcl_09263_grantor;
CREATE ROLE dcl_09263_member;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09263_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_09263_fdw;
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_09263_missing_object TO CURRENT_USER;
BEGIN;
SET ROLE dcl_09263_grantee;
REVOKE INHERIT OPTION FOR USAGE ON FOREIGN DATA WRAPPER dcl_09263_missing_object FROM CURRENT_USER GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT true AS fdw_privilege_statement_completed;
ROLLBACK;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09263_fdw CASCADE;
DROP OWNED BY dcl_09263_grantee;
DROP OWNED BY dcl_09263_member;
DROP OWNED BY dcl_09263_grantor;
DROP ROLE IF EXISTS dcl_09263_member;
DROP ROLE IF EXISTS dcl_09263_grantor;
DROP ROLE IF EXISTS dcl_09263_grantee;
