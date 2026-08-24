-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_7 (foreign_server) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_7
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=role_name
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
DROP ROLE IF EXISTS dcl_03065_grantee;
DROP ROLE IF EXISTS dcl_03065_grantor;
DROP ROLE IF EXISTS dcl_03065_member;
CREATE ROLE dcl_03065_grantee;
CREATE ROLE dcl_03065_grantor;
CREATE ROLE dcl_03065_member;
DROP SERVER IF EXISTS dcl_03065_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_03065_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_03065_fdw;
CREATE SERVER dcl_03065_server FOREIGN DATA WRAPPER dcl_03065_fdw;
BEGIN;
SET ROLE dcl_03065_grantee;
GRANT USAGE ON FOREIGN SERVER dcl_03065_missing_object TO dcl_03065_grantee WITH GRANT OPTION GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'parameter_privilege' AS privilege_scope;
ROLLBACK;
DROP SERVER IF EXISTS dcl_03065_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_03065_fdw CASCADE;
DROP OWNED BY dcl_03065_grantee;
DROP OWNED BY dcl_03065_member;
DROP OWNED BY dcl_03065_grantor;
DROP ROLE IF EXISTS dcl_03065_member;
DROP ROLE IF EXISTS dcl_03065_grantor;
DROP ROLE IF EXISTS dcl_03065_grantee;
