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
DROP ROLE IF EXISTS dcl_09997_grantor;
DROP ROLE IF EXISTS dcl_09997_member;
CREATE ROLE dcl_09997_grantor;
CREATE ROLE dcl_09997_member;
DROP FUNCTION IF EXISTS dcl_09997_function(integer);
CREATE FUNCTION dcl_09997_function(value integer) RETURNS integer LANGUAGE SQL IMMUTABLE RETURN value;
GRANT EXECUTE ON FUNCTION dcl_09997_missing_object(integer) TO dcl_09997_missing_role;
GRANT EXECUTE ON FUNCTION dcl_09997_missing_object(integer) TO dcl_09997_grantor WITH GRANT OPTION;
GRANT dcl_09997_grantor TO dcl_09997_member WITH SET TRUE;
SET ROLE dcl_09997_member;
SET ROLE dcl_09997_grantor;
REVOKE EXECUTE ON FUNCTION dcl_09997_missing_object(integer) FROM dcl_09997_missing_role RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'table_privilege' AS privilege_scope;
RESET ROLE;
RESET ALL;
DROP FUNCTION IF EXISTS dcl_09997_function(integer);
DROP OWNED BY dcl_09997_member;
DROP OWNED BY dcl_09997_grantor;
DROP ROLE IF EXISTS dcl_09997_member;
DROP ROLE IF EXISTS dcl_09997_grantor;
