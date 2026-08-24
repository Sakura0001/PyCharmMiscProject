-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_8 (routine) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_8
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=session_user
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=quoted_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=effect_query
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_10236_Grantee";
DROP ROLE IF EXISTS dcl_10236_grantor;
DROP ROLE IF EXISTS dcl_10236_member;
CREATE ROLE "dcl_10236_Grantee";
CREATE ROLE dcl_10236_grantor;
CREATE ROLE dcl_10236_member;
DROP FUNCTION IF EXISTS dcl_10236_function(integer);
CREATE FUNCTION dcl_10236_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
GRANT EXECUTE ON FUNCTION dcl_10236_missing_object(integer) TO SESSION_USER;
SET ROLE "dcl_10236_Grantee";
REVOKE INHERIT OPTION FOR EXECUTE ON FUNCTION dcl_10236_missing_object(integer) FROM SESSION_USER GRANTED BY dcl_10236_grantor RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
DROP FUNCTION IF EXISTS dcl_10236_function(integer);
DROP OWNED BY "dcl_10236_Grantee";
DROP OWNED BY dcl_10236_member;
DROP OWNED BY dcl_10236_grantor;
DROP ROLE IF EXISTS dcl_10236_member;
DROP ROLE IF EXISTS dcl_10236_grantor;
DROP ROLE IF EXISTS "dcl_10236_Grantee";
