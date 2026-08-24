-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_14 (type) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
-- factor expected_status=success
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=public
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=none
-- factor ownership_boundary=owner
-- factor verification_mode=returned_rows
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS dcl_05892_grantee;
DROP ROLE IF EXISTS dcl_05892_grantor;
DROP ROLE IF EXISTS dcl_05892_member;
CREATE ROLE dcl_05892_grantee;
CREATE ROLE dcl_05892_grantor;
CREATE ROLE dcl_05892_member;
DROP TYPE IF EXISTS dcl_05892_type;
CREATE TYPE dcl_05892_type AS ENUM ('alpha', 'beta');
GRANT USAGE ON TYPE dcl_05892_type TO PUBLIC WITH GRANT OPTION GRANTED BY dcl_05892_grantor;
SELECT 'grant' AS completed_statement, 'routine_language_type_fdw_server' AS privilege_scope;
DROP TYPE IF EXISTS dcl_05892_type;
DROP OWNED BY dcl_05892_grantee;
DROP OWNED BY dcl_05892_member;
DROP OWNED BY dcl_05892_grantor;
DROP ROLE IF EXISTS dcl_05892_member;
DROP ROLE IF EXISTS dcl_05892_grantor;
DROP ROLE IF EXISTS dcl_05892_grantee;
