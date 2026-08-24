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
-- factor grantee_shape=public
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
DROP ROLE IF EXISTS "dcl_09523_Grantee";
DROP ROLE IF EXISTS dcl_09523_grantor;
DROP ROLE IF EXISTS dcl_09523_member;
CREATE ROLE "dcl_09523_Grantee";
CREATE ROLE dcl_09523_grantor;
CREATE ROLE dcl_09523_member;
DROP SERVER IF EXISTS dcl_09523_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09523_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_09523_fdw;
CREATE SERVER dcl_09523_server FOREIGN DATA WRAPPER dcl_09523_fdw;
GRANT USAGE ON FOREIGN SERVER dcl_09523_server TO PUBLIC;
GRANT USAGE ON FOREIGN SERVER dcl_09523_server TO dcl_09523_grantor WITH GRANT OPTION;
SET ROLE dcl_09523_grantor;
REVOKE USAGE ON FOREIGN SERVER dcl_09523_server FROM PUBLIC RESTRICT;
RESET ROLE;
SELECT true AS foreign_server_privilege_statement_completed;
RESET ROLE;
RESET ALL;
DROP SERVER IF EXISTS dcl_09523_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09523_fdw CASCADE;
DROP OWNED BY "dcl_09523_Grantee";
DROP OWNED BY dcl_09523_member;
DROP OWNED BY dcl_09523_grantor;
DROP ROLE IF EXISTS dcl_09523_member;
DROP ROLE IF EXISTS dcl_09523_grantor;
DROP ROLE IF EXISTS "dcl_09523_Grantee";
