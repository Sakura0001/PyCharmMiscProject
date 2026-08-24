-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_3 (sequence) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_3
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=public
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
DROP ROLE IF EXISTS dcl_01157_grantee;
DROP ROLE IF EXISTS dcl_01157_grantor;
DROP ROLE IF EXISTS dcl_01157_member;
CREATE ROLE dcl_01157_grantee;
CREATE ROLE dcl_01157_grantor;
CREATE ROLE dcl_01157_member;
DROP SEQUENCE IF EXISTS dcl_01157_sequence;
CREATE SEQUENCE dcl_01157_sequence;
BEGIN;
SET ROLE dcl_01157_grantee;
GRANT USAGE ON SEQUENCE dcl_01157_missing_object TO PUBLIC WITH GRANT OPTION GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'routine_language_type_fdw_server' AS privilege_scope;
ROLLBACK;
DROP SEQUENCE IF EXISTS dcl_01157_sequence;
DROP OWNED BY dcl_01157_grantee;
DROP OWNED BY dcl_01157_member;
DROP OWNED BY dcl_01157_grantor;
DROP ROLE IF EXISTS dcl_01157_member;
DROP ROLE IF EXISTS dcl_01157_grantor;
DROP ROLE IF EXISTS dcl_01157_grantee;
