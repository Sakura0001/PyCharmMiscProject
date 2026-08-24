-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_10 (large_object) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_10
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=session_user
-- factor grant_option_shape=admin_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=plain_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=effect_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_10952_grantee;
DROP ROLE IF EXISTS dcl_10952_grantor;
DROP ROLE IF EXISTS dcl_10952_member;
CREATE ROLE dcl_10952_grantee;
CREATE ROLE dcl_10952_grantor;
CREATE ROLE dcl_10952_member;
SELECT pg_catalog.lo_unlink(1800000000 + 10) WHERE pg_catalog.lo_open(1800000000 + 10, 131072) IS NOT NULL;
GRANT SELECT ON LARGE OBJECT 1800000010 TO SESSION_USER;
BEGIN;
SET ROLE dcl_10952_grantee;
REVOKE ADMIN OPTION FOR SELECT ON LARGE OBJECT 1800000010 FROM SESSION_USER GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
ROLLBACK;
SELECT pg_catalog.lo_unlink(1800000010);
DROP OWNED BY dcl_10952_grantee;
DROP OWNED BY dcl_10952_member;
DROP OWNED BY dcl_10952_grantor;
DROP ROLE IF EXISTS dcl_10952_member;
DROP ROLE IF EXISTS dcl_10952_grantor;
DROP ROLE IF EXISTS dcl_10952_grantee;
