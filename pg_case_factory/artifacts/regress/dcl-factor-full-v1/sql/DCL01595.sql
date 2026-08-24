-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_4 (database) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_4
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=role_name
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
DROP ROLE IF EXISTS dcl_01595_grantee;
DROP ROLE IF EXISTS dcl_01595_grantor;
DROP ROLE IF EXISTS dcl_01595_member;
CREATE ROLE dcl_01595_grantee;
CREATE ROLE dcl_01595_grantor;
CREATE ROLE dcl_01595_member;
BEGIN;
SET ROLE dcl_01595_grantee;
GRANT CONNECT ON DATABASE dcl_01595_missing_object TO dcl_01595_grantee WITH GRANT OPTION GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT has_database_privilege(CURRENT_USER, 'dcl_01595_database', 'CONNECT');
ROLLBACK;
DROP OWNED BY dcl_01595_grantee;
DROP OWNED BY dcl_01595_member;
DROP OWNED BY dcl_01595_grantor;
DROP ROLE IF EXISTS dcl_01595_member;
DROP ROLE IF EXISTS dcl_01595_grantor;
DROP ROLE IF EXISTS dcl_01595_grantee;
