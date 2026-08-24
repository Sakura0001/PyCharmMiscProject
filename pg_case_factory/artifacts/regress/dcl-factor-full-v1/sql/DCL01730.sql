-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_4 (database) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_4
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=public
-- factor grant_option_shape=admin_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=plain_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=error_assertion
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_01730_grantee;
DROP ROLE IF EXISTS dcl_01730_grantor;
DROP ROLE IF EXISTS dcl_01730_member;
CREATE ROLE dcl_01730_grantee;
CREATE ROLE dcl_01730_grantor;
CREATE ROLE dcl_01730_member;
BEGIN;
SET ROLE dcl_01730_grantee;
GRANT CONNECT ON DATABASE dcl_01730_missing_object TO PUBLIC WITH ADMIN OPTION GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
ROLLBACK;
DROP OWNED BY dcl_01730_grantee;
DROP OWNED BY dcl_01730_member;
DROP OWNED BY dcl_01730_grantor;
DROP ROLE IF EXISTS dcl_01730_member;
DROP ROLE IF EXISTS dcl_01730_grantor;
DROP ROLE IF EXISTS dcl_01730_grantee;
