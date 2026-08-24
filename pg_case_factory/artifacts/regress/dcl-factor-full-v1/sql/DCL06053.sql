-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_14 (type) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=public
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=returned_rows
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_06053_grantee;
DROP ROLE IF EXISTS dcl_06053_grantor;
DROP ROLE IF EXISTS dcl_06053_member;
CREATE ROLE dcl_06053_grantee;
CREATE ROLE dcl_06053_grantor;
CREATE ROLE dcl_06053_member;
DROP TYPE IF EXISTS dcl_06053_type;
CREATE TYPE dcl_06053_type AS ENUM ('alpha', 'beta');
BEGIN;
SET ROLE dcl_06053_grantee;
GRANT USAGE ON TYPE dcl_06053_missing_object TO PUBLIC WITH INHERIT TRUE GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'schema_database_tablespace' AS privilege_scope;
ROLLBACK;
DROP TYPE IF EXISTS dcl_06053_type;
DROP OWNED BY dcl_06053_grantee;
DROP OWNED BY dcl_06053_member;
DROP OWNED BY dcl_06053_grantor;
DROP ROLE IF EXISTS dcl_06053_member;
DROP ROLE IF EXISTS dcl_06053_grantor;
DROP ROLE IF EXISTS dcl_06053_grantee;
