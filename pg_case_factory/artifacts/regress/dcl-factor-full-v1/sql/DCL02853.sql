-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_7 (foreign_server) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_7
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
-- factor grantee_shape=current_role
-- factor grant_option_shape=admin_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=returned_rows
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_02853_Grantee";
DROP ROLE IF EXISTS dcl_02853_grantor;
DROP ROLE IF EXISTS dcl_02853_member;
CREATE ROLE "dcl_02853_Grantee";
CREATE ROLE dcl_02853_grantor;
CREATE ROLE dcl_02853_member;
DROP SERVER IF EXISTS dcl_02853_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02853_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_02853_fdw;
CREATE SERVER dcl_02853_server FOREIGN DATA WRAPPER dcl_02853_fdw;
SET ROLE "dcl_02853_Grantee";
GRANT USAGE ON FOREIGN SERVER dcl_02853_missing_object TO CURRENT_ROLE WITH ADMIN OPTION GRANTED BY dcl_02853_grantor;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'column_privilege' AS privilege_scope;
DROP SERVER IF EXISTS dcl_02853_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02853_fdw CASCADE;
DROP OWNED BY "dcl_02853_Grantee";
DROP OWNED BY dcl_02853_member;
DROP OWNED BY dcl_02853_grantor;
DROP ROLE IF EXISTS dcl_02853_member;
DROP ROLE IF EXISTS dcl_02853_grantor;
DROP ROLE IF EXISTS "dcl_02853_Grantee";
