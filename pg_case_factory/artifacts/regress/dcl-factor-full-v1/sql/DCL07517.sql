-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_2 (column) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=current_user
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=returned_rows
-- factor cleanup_mode=rollback
DROP TABLE IF EXISTS dcl_07517_table;
DROP ROLE IF EXISTS dcl_07517_grantee;
DROP ROLE IF EXISTS dcl_07517_grantor;
DROP ROLE IF EXISTS dcl_07517_member;
CREATE ROLE dcl_07517_grantee;
CREATE ROLE dcl_07517_grantor;
CREATE ROLE dcl_07517_member;
CREATE TABLE dcl_07517_table (id integer, payload text);
GRANT EXECUTE (payload) ON TABLE dcl_07517_missing_object TO CURRENT_USER;
BEGIN;
SET ROLE dcl_07517_grantee;
REVOKE GRANT OPTION FOR EXECUTE (payload) ON TABLE dcl_07517_missing_object FROM CURRENT_USER GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'routine_language_type_fdw_server' AS privilege_scope;
ROLLBACK;
DROP OWNED BY dcl_07517_grantee;
DROP OWNED BY dcl_07517_member;
DROP OWNED BY dcl_07517_grantor;
DROP ROLE IF EXISTS dcl_07517_member;
DROP ROLE IF EXISTS dcl_07517_grantor;
DROP ROLE IF EXISTS dcl_07517_grantee;
DROP TABLE IF EXISTS dcl_07517_table;
