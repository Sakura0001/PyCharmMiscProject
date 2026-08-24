-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_15 (role_membership) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_15
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=session_user
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
DROP ROLE IF EXISTS dcl_06725_grantee;
DROP ROLE IF EXISTS dcl_06725_grantor;
DROP ROLE IF EXISTS dcl_06725_member;
CREATE ROLE dcl_06725_grantee;
CREATE ROLE dcl_06725_grantor;
CREATE ROLE dcl_06725_member;
BEGIN;
SET ROLE dcl_06725_grantee;
GRANT dcl_06725_missing_member TO SESSION_USER WITH INHERIT TRUE GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'parameter_privilege' AS privilege_scope;
ROLLBACK;
DROP OWNED BY dcl_06725_grantee;
DROP OWNED BY dcl_06725_member;
DROP OWNED BY dcl_06725_grantor;
DROP ROLE IF EXISTS dcl_06725_member;
DROP ROLE IF EXISTS dcl_06725_grantor;
DROP ROLE IF EXISTS dcl_06725_grantee;
