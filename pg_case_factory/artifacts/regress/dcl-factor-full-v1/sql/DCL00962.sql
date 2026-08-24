-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_3 (sequence) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_3
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=role_name
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=plain_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=error_assertion
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_00962_grantee;
DROP ROLE IF EXISTS dcl_00962_grantor;
DROP ROLE IF EXISTS dcl_00962_member;
CREATE ROLE dcl_00962_grantee;
CREATE ROLE dcl_00962_grantor;
CREATE ROLE dcl_00962_member;
DROP SEQUENCE IF EXISTS dcl_00962_sequence;
CREATE SEQUENCE dcl_00962_sequence;
BEGIN;
SET ROLE dcl_00962_grantee;
GRANT USAGE ON SEQUENCE dcl_00962_missing_object TO dcl_00962_grantee GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
ROLLBACK;
DROP SEQUENCE IF EXISTS dcl_00962_sequence;
DROP OWNED BY dcl_00962_grantee;
DROP OWNED BY dcl_00962_member;
DROP OWNED BY dcl_00962_grantor;
DROP ROLE IF EXISTS dcl_00962_member;
DROP ROLE IF EXISTS dcl_00962_grantor;
DROP ROLE IF EXISTS dcl_00962_grantee;
