-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_2 (column) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=current_role
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
DROP TABLE IF EXISTS dcl_00545_table;
DROP ROLE IF EXISTS dcl_00545_grantee;
DROP ROLE IF EXISTS dcl_00545_grantor;
DROP ROLE IF EXISTS dcl_00545_member;
CREATE ROLE dcl_00545_grantee;
CREATE ROLE dcl_00545_grantor;
CREATE ROLE dcl_00545_member;
CREATE TABLE dcl_00545_table (id integer, payload text);
BEGIN;
SET ROLE dcl_00545_grantee;
GRANT EXECUTE (payload) ON TABLE dcl_00545_missing_object TO CURRENT_ROLE WITH INHERIT TRUE GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'table_privilege' AS privilege_scope;
ROLLBACK;
DROP OWNED BY dcl_00545_grantee;
DROP OWNED BY dcl_00545_member;
DROP OWNED BY dcl_00545_grantor;
DROP ROLE IF EXISTS dcl_00545_member;
DROP ROLE IF EXISTS dcl_00545_grantor;
DROP ROLE IF EXISTS dcl_00545_grantee;
DROP TABLE IF EXISTS dcl_00545_table;
