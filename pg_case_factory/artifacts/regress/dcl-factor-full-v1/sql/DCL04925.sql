-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_11 (parameter) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_11
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
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
DROP ROLE IF EXISTS dcl_04925_grantee;
DROP ROLE IF EXISTS dcl_04925_grantor;
DROP ROLE IF EXISTS dcl_04925_member;
CREATE ROLE dcl_04925_grantee;
CREATE ROLE dcl_04925_grantor;
CREATE ROLE dcl_04925_member;
BEGIN;
SET ROLE dcl_04925_grantee;
GRANT SELECT ON PARAMETER work_mem TO dcl_04925_grantee WITH GRANT OPTION GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'table_maintain' AS privilege_scope;
ROLLBACK;
DROP OWNED BY dcl_04925_grantee;
DROP OWNED BY dcl_04925_member;
DROP OWNED BY dcl_04925_grantor;
DROP ROLE IF EXISTS dcl_04925_member;
DROP ROLE IF EXISTS dcl_04925_grantor;
DROP ROLE IF EXISTS dcl_04925_grantee;
