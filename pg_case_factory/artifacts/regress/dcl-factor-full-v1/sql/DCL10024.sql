-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_8 (routine) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_8
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=current_role
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
DROP ROLE IF EXISTS dcl_10024_grantor;
DROP ROLE IF EXISTS dcl_10024_member;
CREATE ROLE dcl_10024_grantor;
CREATE ROLE dcl_10024_member;
DROP FUNCTION IF EXISTS dcl_10024_function(integer);
CREATE FUNCTION dcl_10024_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
GRANT EXECUTE ON FUNCTION dcl_10024_missing_object(integer) TO CURRENT_ROLE;
GRANT EXECUTE ON FUNCTION dcl_10024_missing_object(integer) TO dcl_10024_grantor WITH GRANT OPTION;
GRANT dcl_10024_grantor TO dcl_10024_member WITH SET TRUE;
SET ROLE dcl_10024_member;
SET ROLE dcl_10024_grantor;
REVOKE GRANT OPTION FOR EXECUTE ON FUNCTION dcl_10024_missing_object(integer) FROM CURRENT_ROLE RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
RESET ROLE;
RESET ALL;
DROP FUNCTION IF EXISTS dcl_10024_function(integer);
DROP OWNED BY dcl_10024_member;
DROP OWNED BY dcl_10024_grantor;
DROP ROLE IF EXISTS dcl_10024_member;
DROP ROLE IF EXISTS dcl_10024_grantor;
