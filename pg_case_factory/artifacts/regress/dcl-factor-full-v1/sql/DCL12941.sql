-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_14 (type) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
-- factor expected_status=failure
-- factor privilege_scope=role_membership
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
DROP ROLE IF EXISTS dcl_12941_grantee;
DROP ROLE IF EXISTS dcl_12941_grantor;
DROP ROLE IF EXISTS dcl_12941_member;
CREATE ROLE dcl_12941_grantee;
CREATE ROLE dcl_12941_grantor;
CREATE ROLE dcl_12941_member;
DROP TYPE IF EXISTS dcl_12941_type;
CREATE TYPE dcl_12941_type AS ENUM ('alpha', 'beta');
GRANT USAGE ON TYPE dcl_12941_missing_object TO dcl_12941_grantee;
BEGIN;
SET ROLE dcl_12941_grantee;
REVOKE GRANT OPTION FOR USAGE ON TYPE dcl_12941_missing_object FROM dcl_12941_grantee GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'role_membership' AS privilege_scope;
ROLLBACK;
DROP TYPE IF EXISTS dcl_12941_type;
DROP OWNED BY dcl_12941_grantee;
DROP OWNED BY dcl_12941_member;
DROP OWNED BY dcl_12941_grantor;
DROP ROLE IF EXISTS dcl_12941_member;
DROP ROLE IF EXISTS dcl_12941_grantor;
DROP ROLE IF EXISTS dcl_12941_grantee;
