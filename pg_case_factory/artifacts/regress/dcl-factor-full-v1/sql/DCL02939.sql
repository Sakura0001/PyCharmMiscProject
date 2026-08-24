-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_7 (foreign_server) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_7
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
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
DROP ROLE IF EXISTS dcl_02939_grantee;
DROP ROLE IF EXISTS dcl_02939_grantor;
DROP ROLE IF EXISTS dcl_02939_member;
CREATE ROLE dcl_02939_grantee;
CREATE ROLE dcl_02939_grantor;
CREATE ROLE dcl_02939_member;
DROP SERVER IF EXISTS dcl_02939_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02939_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_02939_fdw;
CREATE SERVER dcl_02939_server FOREIGN DATA WRAPPER dcl_02939_fdw;
BEGIN;
SET ROLE dcl_02939_grantee;
GRANT USAGE ON FOREIGN SERVER dcl_02939_missing_object TO SESSION_USER WITH INHERIT TRUE GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT true AS foreign_server_privilege_statement_completed;
ROLLBACK;
DROP SERVER IF EXISTS dcl_02939_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02939_fdw CASCADE;
DROP OWNED BY dcl_02939_grantee;
DROP OWNED BY dcl_02939_member;
DROP OWNED BY dcl_02939_grantor;
DROP ROLE IF EXISTS dcl_02939_member;
DROP ROLE IF EXISTS dcl_02939_grantor;
DROP ROLE IF EXISTS dcl_02939_grantee;
