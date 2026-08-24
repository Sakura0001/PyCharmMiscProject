-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_7 (foreign_server) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_7
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
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
DROP ROLE IF EXISTS dcl_09851_grantee;
DROP ROLE IF EXISTS dcl_09851_grantor;
DROP ROLE IF EXISTS dcl_09851_member;
CREATE ROLE dcl_09851_grantee;
CREATE ROLE dcl_09851_grantor;
CREATE ROLE dcl_09851_member;
DROP SERVER IF EXISTS dcl_09851_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09851_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_09851_fdw;
CREATE SERVER dcl_09851_server FOREIGN DATA WRAPPER dcl_09851_fdw;
GRANT USAGE ON FOREIGN SERVER dcl_09851_missing_object TO dcl_09851_grantee;
BEGIN;
SET ROLE dcl_09851_grantee;
REVOKE GRANT OPTION FOR USAGE ON FOREIGN SERVER dcl_09851_missing_object FROM dcl_09851_grantee GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT true AS foreign_server_privilege_statement_completed;
ROLLBACK;
DROP SERVER IF EXISTS dcl_09851_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09851_fdw CASCADE;
DROP OWNED BY dcl_09851_grantee;
DROP OWNED BY dcl_09851_member;
DROP OWNED BY dcl_09851_grantor;
DROP ROLE IF EXISTS dcl_09851_member;
DROP ROLE IF EXISTS dcl_09851_grantor;
DROP ROLE IF EXISTS dcl_09851_grantee;
