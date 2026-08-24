-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_2 (column) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
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
DROP TABLE IF EXISTS dcl_00713_table;
DROP ROLE IF EXISTS dcl_00713_grantee;
DROP ROLE IF EXISTS dcl_00713_grantor;
DROP ROLE IF EXISTS dcl_00713_member;
CREATE ROLE dcl_00713_grantee;
CREATE ROLE dcl_00713_grantor;
CREATE ROLE dcl_00713_member;
CREATE TABLE dcl_00713_table (id integer, payload text);
BEGIN;
SET ROLE dcl_00713_grantee;
GRANT EXECUTE (payload) ON TABLE dcl_00713_missing_object TO PUBLIC WITH INHERIT TRUE GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'routine_language_type_fdw_server' AS privilege_scope;
ROLLBACK;
DROP OWNED BY dcl_00713_grantee;
DROP OWNED BY dcl_00713_member;
DROP OWNED BY dcl_00713_grantor;
DROP ROLE IF EXISTS dcl_00713_member;
DROP ROLE IF EXISTS dcl_00713_grantor;
DROP ROLE IF EXISTS dcl_00713_grantee;
DROP TABLE IF EXISTS dcl_00713_table;
