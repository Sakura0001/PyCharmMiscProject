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
-- factor grantee_shape=public
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=returned_rows
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_12833_grantee;
DROP ROLE IF EXISTS dcl_12833_grantor;
DROP ROLE IF EXISTS dcl_12833_member;
CREATE ROLE dcl_12833_grantee;
CREATE ROLE dcl_12833_grantor;
CREATE ROLE dcl_12833_member;
DROP TYPE IF EXISTS dcl_12833_type;
CREATE TYPE dcl_12833_type AS ENUM ('alpha', 'beta');
GRANT USAGE ON TYPE dcl_12833_missing_object TO PUBLIC;
BEGIN;
SET ROLE dcl_12833_grantee;
REVOKE GRANT OPTION FOR USAGE ON TYPE dcl_12833_missing_object FROM PUBLIC GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'schema_database_tablespace' AS privilege_scope;
ROLLBACK;
DROP TYPE IF EXISTS dcl_12833_type;
DROP OWNED BY dcl_12833_grantee;
DROP OWNED BY dcl_12833_member;
DROP OWNED BY dcl_12833_grantor;
DROP ROLE IF EXISTS dcl_12833_member;
DROP ROLE IF EXISTS dcl_12833_grantor;
DROP ROLE IF EXISTS dcl_12833_grantee;
