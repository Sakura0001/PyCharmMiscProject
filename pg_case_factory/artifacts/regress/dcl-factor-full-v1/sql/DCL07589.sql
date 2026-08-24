-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_2 (column) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=session_user
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
DROP TABLE IF EXISTS dcl_07589_table;
DROP ROLE IF EXISTS dcl_07589_grantee;
DROP ROLE IF EXISTS dcl_07589_grantor;
DROP ROLE IF EXISTS dcl_07589_member;
CREATE ROLE dcl_07589_grantee;
CREATE ROLE dcl_07589_grantor;
CREATE ROLE dcl_07589_member;
CREATE TABLE dcl_07589_table (id integer, payload text);
GRANT EXECUTE (payload) ON TABLE dcl_07589_missing_object TO SESSION_USER;
BEGIN;
SET ROLE dcl_07589_grantee;
REVOKE GRANT OPTION FOR EXECUTE (payload) ON TABLE dcl_07589_missing_object FROM SESSION_USER GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'role_membership' AS privilege_scope;
ROLLBACK;
DROP OWNED BY dcl_07589_grantee;
DROP OWNED BY dcl_07589_member;
DROP OWNED BY dcl_07589_grantor;
DROP ROLE IF EXISTS dcl_07589_member;
DROP ROLE IF EXISTS dcl_07589_grantor;
DROP ROLE IF EXISTS dcl_07589_grantee;
DROP TABLE IF EXISTS dcl_07589_table;
