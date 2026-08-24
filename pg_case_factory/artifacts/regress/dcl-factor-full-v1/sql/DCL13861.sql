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
-- factor expected_status=success
-- factor privilege_scope=table_privilege
-- factor grantee_shape=role_name
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=none
-- factor ownership_boundary=owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS dcl_13861_grantee;
DROP ROLE IF EXISTS dcl_13861_grantor;
DROP ROLE IF EXISTS dcl_13861_member;
CREATE ROLE dcl_13861_grantee;
CREATE ROLE dcl_13861_grantor;
CREATE ROLE dcl_13861_member;
DROP FUNCTION IF EXISTS dcl_13861_function(integer);
CREATE FUNCTION dcl_13861_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
GRANT EXECUTE ON FUNCTION dcl_13861_function(integer) TO dcl_13861_grantee;
REVOKE EXECUTE ON FUNCTION dcl_13861_function(integer) FROM dcl_13861_grantee RESTRICT;
SELECT has_function_privilege(CURRENT_USER, 'dcl_13861_function(integer)', 'EXECUTE');
DROP FUNCTION IF EXISTS dcl_13861_function(integer);
DROP OWNED BY dcl_13861_grantee;
DROP OWNED BY dcl_13861_member;
DROP OWNED BY dcl_13861_grantor;
DROP ROLE IF EXISTS dcl_13861_member;
DROP ROLE IF EXISTS dcl_13861_grantor;
DROP ROLE IF EXISTS dcl_13861_grantee;
