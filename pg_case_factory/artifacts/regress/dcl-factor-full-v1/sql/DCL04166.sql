-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_10 (large_object) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_10
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=session_user
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
DROP ROLE IF EXISTS dcl_04166_grantee;
DROP ROLE IF EXISTS dcl_04166_grantor;
DROP ROLE IF EXISTS dcl_04166_member;
CREATE ROLE dcl_04166_grantee;
CREATE ROLE dcl_04166_grantor;
CREATE ROLE dcl_04166_member;
SELECT pg_catalog.lo_unlink(1800000000 + 10) WHERE pg_catalog.lo_open(1800000000 + 10, 131072) IS NOT NULL;
BEGIN;
SET ROLE dcl_04166_grantee;
GRANT SELECT ON LARGE OBJECT 1800000010 TO SESSION_USER WITH ADMIN OPTION GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
ROLLBACK;
SELECT pg_catalog.lo_unlink(1800000010);
DROP OWNED BY dcl_04166_grantee;
DROP OWNED BY dcl_04166_member;
DROP OWNED BY dcl_04166_grantor;
DROP ROLE IF EXISTS dcl_04166_member;
DROP ROLE IF EXISTS dcl_04166_grantor;
DROP ROLE IF EXISTS dcl_04166_grantee;
