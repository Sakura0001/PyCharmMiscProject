-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_10 (large_object) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_10
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=current_user
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=missing_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=effect_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_04456_grantor;
DROP ROLE IF EXISTS dcl_04456_member;
CREATE ROLE dcl_04456_grantor;
CREATE ROLE dcl_04456_member;
SELECT pg_catalog.lo_unlink(1800000000 + 10) WHERE pg_catalog.lo_open(1800000000 + 10, 131072) IS NOT NULL;
GRANT SELECT ON LARGE OBJECT 1800000010 TO dcl_04456_grantor WITH GRANT OPTION;
GRANT dcl_04456_grantor TO dcl_04456_member WITH SET TRUE;
SET ROLE dcl_04456_member;
SET ROLE dcl_04456_grantor;
GRANT SELECT ON LARGE OBJECT 1800000010 TO CURRENT_USER WITH INHERIT TRUE;
RESET ROLE;
SELECT true AS privilege_effect_observed;
RESET ROLE;
RESET ALL;
SELECT pg_catalog.lo_unlink(1800000010);
DROP OWNED BY dcl_04456_member;
DROP OWNED BY dcl_04456_grantor;
DROP ROLE IF EXISTS dcl_04456_member;
DROP ROLE IF EXISTS dcl_04456_grantor;
