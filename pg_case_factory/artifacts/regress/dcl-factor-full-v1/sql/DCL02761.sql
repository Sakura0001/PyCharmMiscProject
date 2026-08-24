-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_7 (foreign_server) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_7
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=role_name
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=missing_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=returned_rows
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_02761_grantor;
DROP ROLE IF EXISTS dcl_02761_member;
CREATE ROLE dcl_02761_grantor;
CREATE ROLE dcl_02761_member;
DROP SERVER IF EXISTS dcl_02761_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02761_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_02761_fdw;
CREATE SERVER dcl_02761_server FOREIGN DATA WRAPPER dcl_02761_fdw;
GRANT USAGE ON FOREIGN SERVER dcl_02761_missing_object TO dcl_02761_grantor WITH GRANT OPTION;
GRANT dcl_02761_grantor TO dcl_02761_member WITH SET TRUE;
SET ROLE dcl_02761_member;
SET ROLE dcl_02761_grantor;
GRANT USAGE ON FOREIGN SERVER dcl_02761_missing_object TO dcl_02761_missing_role;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'table_privilege' AS privilege_scope;
RESET ROLE;
RESET ALL;
DROP SERVER IF EXISTS dcl_02761_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02761_fdw CASCADE;
DROP OWNED BY dcl_02761_member;
DROP OWNED BY dcl_02761_grantor;
DROP ROLE IF EXISTS dcl_02761_member;
DROP ROLE IF EXISTS dcl_02761_grantor;
