-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_7 (foreign_server) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_7
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
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
DROP ROLE IF EXISTS dcl_09935_grantee;
DROP ROLE IF EXISTS dcl_09935_grantor;
DROP ROLE IF EXISTS dcl_09935_member;
CREATE ROLE dcl_09935_grantee;
CREATE ROLE dcl_09935_grantor;
CREATE ROLE dcl_09935_member;
DROP SERVER IF EXISTS dcl_09935_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09935_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_09935_fdw;
CREATE SERVER dcl_09935_server FOREIGN DATA WRAPPER dcl_09935_fdw;
GRANT USAGE ON FOREIGN SERVER dcl_09935_missing_object TO CURRENT_ROLE;
BEGIN;
SET ROLE dcl_09935_grantee;
REVOKE GRANT OPTION FOR USAGE ON FOREIGN SERVER dcl_09935_missing_object FROM CURRENT_ROLE GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT true AS foreign_server_privilege_statement_completed;
ROLLBACK;
DROP SERVER IF EXISTS dcl_09935_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09935_fdw CASCADE;
DROP OWNED BY dcl_09935_grantee;
DROP OWNED BY dcl_09935_member;
DROP OWNED BY dcl_09935_grantor;
DROP ROLE IF EXISTS dcl_09935_member;
DROP ROLE IF EXISTS dcl_09935_grantor;
DROP ROLE IF EXISTS dcl_09935_grantee;
