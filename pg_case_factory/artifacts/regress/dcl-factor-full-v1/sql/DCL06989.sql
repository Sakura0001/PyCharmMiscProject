-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_1 (table) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=public
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=returned_rows
-- factor cleanup_mode=rollback
DROP TABLE IF EXISTS dcl_06989_table;
DROP ROLE IF EXISTS dcl_06989_grantee;
DROP ROLE IF EXISTS dcl_06989_grantor;
DROP ROLE IF EXISTS dcl_06989_member;
CREATE ROLE dcl_06989_grantee;
CREATE ROLE dcl_06989_grantor;
CREATE ROLE dcl_06989_member;
CREATE TABLE dcl_06989_table (id integer, payload text);
GRANT SELECT ON TABLE dcl_06989_missing_object TO PUBLIC;
BEGIN;
SET ROLE dcl_06989_grantee;
REVOKE INHERIT OPTION FOR SELECT ON TABLE dcl_06989_missing_object FROM PUBLIC GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'schema_database_tablespace' AS privilege_scope;
ROLLBACK;
DROP OWNED BY dcl_06989_grantee;
DROP OWNED BY dcl_06989_member;
DROP OWNED BY dcl_06989_grantor;
DROP ROLE IF EXISTS dcl_06989_member;
DROP ROLE IF EXISTS dcl_06989_grantor;
DROP ROLE IF EXISTS dcl_06989_grantee;
DROP TABLE IF EXISTS dcl_06989_table;
