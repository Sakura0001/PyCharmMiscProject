-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_7 (foreign_server) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_7
-- factor expected_status=success
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=current_role
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
DROP ROLE IF EXISTS "dcl_02743_Grantee";
DROP ROLE IF EXISTS dcl_02743_grantor;
DROP ROLE IF EXISTS dcl_02743_member;
CREATE ROLE "dcl_02743_Grantee";
CREATE ROLE dcl_02743_grantor;
CREATE ROLE dcl_02743_member;
DROP SERVER IF EXISTS dcl_02743_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02743_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_02743_fdw;
CREATE SERVER dcl_02743_server FOREIGN DATA WRAPPER dcl_02743_fdw;
GRANT USAGE ON FOREIGN SERVER dcl_02743_server TO dcl_02743_grantor WITH GRANT OPTION;
SET ROLE dcl_02743_grantor;
GRANT USAGE ON FOREIGN SERVER dcl_02743_server TO CURRENT_ROLE;
RESET ROLE;
SELECT true AS foreign_server_privilege_statement_completed;
RESET ROLE;
RESET ALL;
DROP SERVER IF EXISTS dcl_02743_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02743_fdw CASCADE;
DROP OWNED BY "dcl_02743_Grantee";
DROP OWNED BY dcl_02743_member;
DROP OWNED BY dcl_02743_grantor;
DROP ROLE IF EXISTS dcl_02743_member;
DROP ROLE IF EXISTS dcl_02743_grantor;
DROP ROLE IF EXISTS "dcl_02743_Grantee";
