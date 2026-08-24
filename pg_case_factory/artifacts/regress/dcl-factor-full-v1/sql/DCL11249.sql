-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_10 (large_object) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_10
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
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
DROP ROLE IF EXISTS dcl_11249_grantee;
DROP ROLE IF EXISTS dcl_11249_grantor;
DROP ROLE IF EXISTS dcl_11249_member;
CREATE ROLE dcl_11249_grantee;
CREATE ROLE dcl_11249_grantor;
CREATE ROLE dcl_11249_member;
SELECT pg_catalog.lo_unlink(1800000000 + 10) WHERE pg_catalog.lo_open(1800000000 + 10, 131072) IS NOT NULL;
GRANT SELECT ON LARGE OBJECT 1800000010 TO SESSION_USER;
BEGIN;
SET ROLE dcl_11249_grantee;
REVOKE GRANT OPTION FOR SELECT ON LARGE OBJECT 1800000010 FROM SESSION_USER GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'parameter_privilege' AS privilege_scope;
ROLLBACK;
SELECT pg_catalog.lo_unlink(1800000010);
DROP OWNED BY dcl_11249_grantee;
DROP OWNED BY dcl_11249_member;
DROP OWNED BY dcl_11249_grantor;
DROP ROLE IF EXISTS dcl_11249_member;
DROP ROLE IF EXISTS dcl_11249_grantor;
DROP ROLE IF EXISTS dcl_11249_grantee;
