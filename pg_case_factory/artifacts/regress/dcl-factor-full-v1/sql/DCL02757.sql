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
-- factor grantee_shape=session_user
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=member_role
-- factor verification_mode=returned_rows
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_02757_Grantee";
DROP ROLE IF EXISTS dcl_02757_grantor;
DROP ROLE IF EXISTS dcl_02757_member;
CREATE ROLE "dcl_02757_Grantee";
CREATE ROLE dcl_02757_grantor;
CREATE ROLE dcl_02757_member;
DROP SERVER IF EXISTS dcl_02757_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02757_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_02757_fdw;
CREATE SERVER dcl_02757_server FOREIGN DATA WRAPPER dcl_02757_fdw;
GRANT USAGE ON FOREIGN SERVER dcl_02757_server TO dcl_02757_grantor WITH GRANT OPTION;
SET ROLE dcl_02757_grantor;
GRANT USAGE ON FOREIGN SERVER dcl_02757_server TO SESSION_USER GRANTED BY dcl_02757_grantor;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'routine_language_type_fdw_server' AS privilege_scope;
DROP SERVER IF EXISTS dcl_02757_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02757_fdw CASCADE;
DROP OWNED BY "dcl_02757_Grantee";
DROP OWNED BY dcl_02757_member;
DROP OWNED BY dcl_02757_grantor;
DROP ROLE IF EXISTS dcl_02757_member;
DROP ROLE IF EXISTS dcl_02757_grantor;
DROP ROLE IF EXISTS "dcl_02757_Grantee";
