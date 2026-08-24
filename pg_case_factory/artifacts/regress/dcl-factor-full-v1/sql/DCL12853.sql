-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_14 (type) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=current_user
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
DROP ROLE IF EXISTS dcl_12853_grantor;
DROP ROLE IF EXISTS dcl_12853_member;
CREATE ROLE dcl_12853_grantor;
CREATE ROLE dcl_12853_member;
DROP TYPE IF EXISTS dcl_12853_type;
CREATE TYPE dcl_12853_type AS ENUM ('alpha', 'beta');
GRANT USAGE ON TYPE dcl_12853_missing_object TO CURRENT_USER;
GRANT USAGE ON TYPE dcl_12853_missing_object TO dcl_12853_grantor WITH GRANT OPTION;
GRANT dcl_12853_grantor TO dcl_12853_member WITH SET TRUE;
SET ROLE dcl_12853_member;
SET ROLE dcl_12853_grantor;
REVOKE USAGE ON TYPE dcl_12853_missing_object FROM CURRENT_USER RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'schema_database_tablespace' AS privilege_scope;
RESET ROLE;
RESET ALL;
DROP TYPE IF EXISTS dcl_12853_type;
DROP OWNED BY dcl_12853_member;
DROP OWNED BY dcl_12853_grantor;
DROP ROLE IF EXISTS dcl_12853_member;
DROP ROLE IF EXISTS dcl_12853_grantor;
