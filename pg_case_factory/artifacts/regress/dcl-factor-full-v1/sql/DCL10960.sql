-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_10 (large_object) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_10
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
-- factor grantee_shape=role_name
-- factor grant_option_shape=grant_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=missing_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=effect_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_10960_grantor;
DROP ROLE IF EXISTS dcl_10960_member;
CREATE ROLE dcl_10960_grantor;
CREATE ROLE dcl_10960_member;
SELECT pg_catalog.lo_unlink(1800000000 + 10) WHERE pg_catalog.lo_open(1800000000 + 10, 131072) IS NOT NULL;
GRANT SELECT ON LARGE OBJECT 1800000010 TO dcl_10960_missing_role;
GRANT SELECT ON LARGE OBJECT 1800000010 TO dcl_10960_grantor WITH GRANT OPTION;
GRANT dcl_10960_grantor TO dcl_10960_member WITH SET TRUE;
SET ROLE dcl_10960_member;
SET ROLE dcl_10960_grantor;
REVOKE GRANT OPTION FOR SELECT ON LARGE OBJECT 1800000010 FROM dcl_10960_missing_role RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
RESET ROLE;
RESET ALL;
SELECT pg_catalog.lo_unlink(1800000010);
DROP OWNED BY dcl_10960_member;
DROP OWNED BY dcl_10960_grantor;
DROP ROLE IF EXISTS dcl_10960_member;
DROP ROLE IF EXISTS dcl_10960_grantor;
