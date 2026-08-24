-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_8 (routine) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_8
-- factor expected_status=failure
-- factor privilege_scope=role_membership
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
DROP ROLE IF EXISTS dcl_10240_grantor;
DROP ROLE IF EXISTS dcl_10240_member;
CREATE ROLE dcl_10240_grantor;
CREATE ROLE dcl_10240_member;
DROP FUNCTION IF EXISTS dcl_10240_function(integer);
CREATE FUNCTION dcl_10240_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
GRANT EXECUTE ON FUNCTION dcl_10240_missing_object(integer) TO dcl_10240_missing_role;
GRANT EXECUTE ON FUNCTION dcl_10240_missing_object(integer) TO dcl_10240_grantor WITH GRANT OPTION;
GRANT dcl_10240_grantor TO dcl_10240_member WITH SET TRUE;
SET ROLE dcl_10240_member;
SET ROLE dcl_10240_grantor;
REVOKE GRANT OPTION FOR EXECUTE ON FUNCTION dcl_10240_missing_object(integer) FROM dcl_10240_missing_role RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
RESET ROLE;
RESET ALL;
DROP FUNCTION IF EXISTS dcl_10240_function(integer);
DROP OWNED BY dcl_10240_member;
DROP OWNED BY dcl_10240_grantor;
DROP ROLE IF EXISTS dcl_10240_member;
DROP ROLE IF EXISTS dcl_10240_grantor;
