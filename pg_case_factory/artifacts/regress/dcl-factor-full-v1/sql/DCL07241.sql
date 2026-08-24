-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_1 (table) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
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
DROP TABLE IF EXISTS dcl_07241_table;
DROP ROLE IF EXISTS dcl_07241_grantee;
DROP ROLE IF EXISTS dcl_07241_grantor;
DROP ROLE IF EXISTS dcl_07241_member;
CREATE ROLE dcl_07241_grantee;
CREATE ROLE dcl_07241_grantor;
CREATE ROLE dcl_07241_member;
CREATE TABLE dcl_07241_table (id integer, payload text);
GRANT MAINTAIN ON TABLE dcl_07241_missing_object TO CURRENT_ROLE;
BEGIN;
SET ROLE dcl_07241_grantee;
REVOKE INHERIT OPTION FOR MAINTAIN ON TABLE dcl_07241_missing_object FROM CURRENT_ROLE GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'table_maintain' AS privilege_scope;
ROLLBACK;
DROP OWNED BY dcl_07241_grantee;
DROP OWNED BY dcl_07241_member;
DROP OWNED BY dcl_07241_grantor;
DROP ROLE IF EXISTS dcl_07241_member;
DROP ROLE IF EXISTS dcl_07241_grantor;
DROP ROLE IF EXISTS dcl_07241_grantee;
DROP TABLE IF EXISTS dcl_07241_table;
