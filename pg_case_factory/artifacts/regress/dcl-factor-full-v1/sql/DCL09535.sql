-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_7 (foreign_server) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_7
-- factor expected_status=success
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=current_user
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=member_role
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS "dcl_09535_Grantee";
DROP ROLE IF EXISTS dcl_09535_grantor;
DROP ROLE IF EXISTS dcl_09535_member;
CREATE ROLE "dcl_09535_Grantee";
CREATE ROLE dcl_09535_grantor;
CREATE ROLE dcl_09535_member;
DROP SERVER IF EXISTS dcl_09535_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09535_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_09535_fdw;
CREATE SERVER dcl_09535_server FOREIGN DATA WRAPPER dcl_09535_fdw;
GRANT USAGE ON FOREIGN SERVER dcl_09535_server TO CURRENT_USER;
GRANT USAGE ON FOREIGN SERVER dcl_09535_server TO dcl_09535_grantor WITH GRANT OPTION;
SET ROLE dcl_09535_grantor;
REVOKE USAGE ON FOREIGN SERVER dcl_09535_server FROM CURRENT_USER RESTRICT;
RESET ROLE;
SELECT true AS foreign_server_privilege_statement_completed;
RESET ROLE;
RESET ALL;
DROP SERVER IF EXISTS dcl_09535_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09535_fdw CASCADE;
DROP OWNED BY "dcl_09535_Grantee";
DROP OWNED BY dcl_09535_member;
DROP OWNED BY dcl_09535_grantor;
DROP ROLE IF EXISTS dcl_09535_member;
DROP ROLE IF EXISTS dcl_09535_grantor;
DROP ROLE IF EXISTS "dcl_09535_Grantee";
