-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_6 (foreign_data_wrapper) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_6
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=current_user
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
DROP ROLE IF EXISTS dcl_02357_grantee;
DROP ROLE IF EXISTS dcl_02357_grantor;
DROP ROLE IF EXISTS dcl_02357_member;
CREATE ROLE dcl_02357_grantee;
CREATE ROLE dcl_02357_grantor;
CREATE ROLE dcl_02357_member;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02357_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_02357_fdw;
BEGIN;
SET ROLE dcl_02357_grantee;
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_02357_missing_object TO CURRENT_USER WITH INHERIT TRUE GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'table_privilege' AS privilege_scope;
ROLLBACK;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02357_fdw CASCADE;
DROP OWNED BY dcl_02357_grantee;
DROP OWNED BY dcl_02357_member;
DROP OWNED BY dcl_02357_grantor;
DROP ROLE IF EXISTS dcl_02357_member;
DROP ROLE IF EXISTS dcl_02357_grantor;
DROP ROLE IF EXISTS dcl_02357_grantee;
