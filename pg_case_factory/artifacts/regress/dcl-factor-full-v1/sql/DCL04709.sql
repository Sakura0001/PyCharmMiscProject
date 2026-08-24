-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_11 (parameter) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_11
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=current_role
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
DROP ROLE IF EXISTS dcl_04709_grantee;
DROP ROLE IF EXISTS dcl_04709_grantor;
DROP ROLE IF EXISTS dcl_04709_member;
CREATE ROLE dcl_04709_grantee;
CREATE ROLE dcl_04709_grantor;
CREATE ROLE dcl_04709_member;
BEGIN;
SET ROLE dcl_04709_grantee;
GRANT SELECT ON PARAMETER work_mem TO CURRENT_ROLE WITH GRANT OPTION GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'schema_database_tablespace' AS privilege_scope;
ROLLBACK;
DROP OWNED BY dcl_04709_grantee;
DROP OWNED BY dcl_04709_member;
DROP OWNED BY dcl_04709_grantor;
DROP ROLE IF EXISTS dcl_04709_member;
DROP ROLE IF EXISTS dcl_04709_grantor;
DROP ROLE IF EXISTS dcl_04709_grantee;
