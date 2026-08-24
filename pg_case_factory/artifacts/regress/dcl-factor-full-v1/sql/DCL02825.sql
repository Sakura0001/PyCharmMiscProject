-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_7 (foreign_server) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_7
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
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
DROP ROLE IF EXISTS dcl_02825_grantee;
DROP ROLE IF EXISTS dcl_02825_grantor;
DROP ROLE IF EXISTS dcl_02825_member;
CREATE ROLE dcl_02825_grantee;
CREATE ROLE dcl_02825_grantor;
CREATE ROLE dcl_02825_member;
DROP SERVER IF EXISTS dcl_02825_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02825_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_02825_fdw;
CREATE SERVER dcl_02825_server FOREIGN DATA WRAPPER dcl_02825_fdw;
BEGIN;
SET ROLE dcl_02825_grantee;
GRANT USAGE ON FOREIGN SERVER dcl_02825_missing_object TO dcl_02825_grantee WITH GRANT OPTION GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'column_privilege' AS privilege_scope;
ROLLBACK;
DROP SERVER IF EXISTS dcl_02825_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02825_fdw CASCADE;
DROP OWNED BY dcl_02825_grantee;
DROP OWNED BY dcl_02825_member;
DROP OWNED BY dcl_02825_grantor;
DROP ROLE IF EXISTS dcl_02825_member;
DROP ROLE IF EXISTS dcl_02825_grantor;
DROP ROLE IF EXISTS dcl_02825_grantee;
