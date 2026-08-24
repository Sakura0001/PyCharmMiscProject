-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_4 (database) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_4
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
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
DROP ROLE IF EXISTS dcl_08423_grantee;
DROP ROLE IF EXISTS dcl_08423_grantor;
DROP ROLE IF EXISTS dcl_08423_member;
CREATE ROLE dcl_08423_grantee;
CREATE ROLE dcl_08423_grantor;
CREATE ROLE dcl_08423_member;
GRANT CONNECT ON DATABASE dcl_08423_missing_object TO CURRENT_USER;
BEGIN;
SET ROLE dcl_08423_grantee;
REVOKE INHERIT OPTION FOR CONNECT ON DATABASE dcl_08423_missing_object FROM CURRENT_USER GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT has_database_privilege(CURRENT_USER, 'dcl_08423_database', 'CONNECT');
ROLLBACK;
DROP OWNED BY dcl_08423_grantee;
DROP OWNED BY dcl_08423_member;
DROP OWNED BY dcl_08423_grantor;
DROP ROLE IF EXISTS dcl_08423_member;
DROP ROLE IF EXISTS dcl_08423_grantor;
DROP ROLE IF EXISTS dcl_08423_grantee;
