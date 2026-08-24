-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_8 (routine) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_8
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
-- factor grantee_shape=role_name
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=missing_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=returned_rows
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_10057_grantor;
DROP ROLE IF EXISTS dcl_10057_member;
CREATE ROLE dcl_10057_grantor;
CREATE ROLE dcl_10057_member;
DROP FUNCTION IF EXISTS dcl_10057_function(integer);
CREATE FUNCTION dcl_10057_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
GRANT EXECUTE ON FUNCTION dcl_10057_missing_object(integer) TO dcl_10057_missing_role;
GRANT EXECUTE ON FUNCTION dcl_10057_missing_object(integer) TO dcl_10057_grantor WITH GRANT OPTION;
GRANT dcl_10057_grantor TO dcl_10057_member WITH SET TRUE;
SET ROLE dcl_10057_member;
SET ROLE dcl_10057_grantor;
REVOKE EXECUTE ON FUNCTION dcl_10057_missing_object(integer) FROM dcl_10057_missing_role RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'column_privilege' AS privilege_scope;
RESET ROLE;
RESET ALL;
DROP FUNCTION IF EXISTS dcl_10057_function(integer);
DROP OWNED BY dcl_10057_member;
DROP OWNED BY dcl_10057_grantor;
DROP ROLE IF EXISTS dcl_10057_member;
DROP ROLE IF EXISTS dcl_10057_grantor;
