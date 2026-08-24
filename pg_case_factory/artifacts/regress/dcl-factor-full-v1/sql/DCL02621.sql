-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_6 (foreign_data_wrapper) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_6
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=role_name
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
DROP ROLE IF EXISTS dcl_02621_grantee;
DROP ROLE IF EXISTS dcl_02621_grantor;
DROP ROLE IF EXISTS dcl_02621_member;
CREATE ROLE dcl_02621_grantee;
CREATE ROLE dcl_02621_grantor;
CREATE ROLE dcl_02621_member;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02621_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_02621_fdw;
BEGIN;
SET ROLE dcl_02621_grantee;
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_02621_missing_object TO dcl_02621_grantee WITH INHERIT TRUE GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'parameter_privilege' AS privilege_scope;
ROLLBACK;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02621_fdw CASCADE;
DROP OWNED BY dcl_02621_grantee;
DROP OWNED BY dcl_02621_member;
DROP OWNED BY dcl_02621_grantor;
DROP ROLE IF EXISTS dcl_02621_member;
DROP ROLE IF EXISTS dcl_02621_grantor;
DROP ROLE IF EXISTS dcl_02621_grantee;
