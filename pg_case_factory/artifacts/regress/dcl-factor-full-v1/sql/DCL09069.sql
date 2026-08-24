-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_6 (foreign_data_wrapper) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_6
-- factor expected_status=success
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=role_name
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
DROP ROLE IF EXISTS "dcl_09069_Grantee";
DROP ROLE IF EXISTS dcl_09069_grantor;
DROP ROLE IF EXISTS dcl_09069_member;
CREATE ROLE "dcl_09069_Grantee";
CREATE ROLE dcl_09069_grantor;
CREATE ROLE dcl_09069_member;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09069_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_09069_fdw;
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_09069_fdw TO "dcl_09069_Grantee";
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_09069_fdw TO dcl_09069_grantor WITH GRANT OPTION;
SET ROLE dcl_09069_grantor;
REVOKE USAGE ON FOREIGN DATA WRAPPER dcl_09069_fdw FROM "dcl_09069_Grantee" GRANTED BY dcl_09069_grantor RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'routine_language_type_fdw_server' AS privilege_scope;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09069_fdw CASCADE;
DROP OWNED BY "dcl_09069_Grantee";
DROP OWNED BY dcl_09069_member;
DROP OWNED BY dcl_09069_grantor;
DROP ROLE IF EXISTS dcl_09069_member;
DROP ROLE IF EXISTS dcl_09069_grantor;
DROP ROLE IF EXISTS "dcl_09069_Grantee";
