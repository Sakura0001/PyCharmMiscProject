-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_7 (foreign_server) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_7
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=role_name
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=returned_rows
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_09549_Grantee";
DROP ROLE IF EXISTS dcl_09549_grantor;
DROP ROLE IF EXISTS dcl_09549_member;
CREATE ROLE "dcl_09549_Grantee";
CREATE ROLE dcl_09549_grantor;
CREATE ROLE dcl_09549_member;
DROP SERVER IF EXISTS dcl_09549_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09549_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_09549_fdw;
CREATE SERVER dcl_09549_server FOREIGN DATA WRAPPER dcl_09549_fdw;
GRANT USAGE ON FOREIGN SERVER dcl_09549_missing_object TO "dcl_09549_Grantee";
SET ROLE "dcl_09549_Grantee";
REVOKE USAGE ON FOREIGN SERVER dcl_09549_missing_object FROM "dcl_09549_Grantee" GRANTED BY dcl_09549_grantor RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'table_privilege' AS privilege_scope;
DROP SERVER IF EXISTS dcl_09549_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09549_fdw CASCADE;
DROP OWNED BY "dcl_09549_Grantee";
DROP OWNED BY dcl_09549_member;
DROP OWNED BY dcl_09549_grantor;
DROP ROLE IF EXISTS dcl_09549_member;
DROP ROLE IF EXISTS dcl_09549_grantor;
DROP ROLE IF EXISTS "dcl_09549_Grantee";
