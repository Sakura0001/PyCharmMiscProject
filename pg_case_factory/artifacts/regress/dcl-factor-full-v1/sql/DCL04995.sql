-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_12 (schema) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_12
-- factor expected_status=success
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=current_role
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=member_role
-- factor verification_mode=returned_rows
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_04995_Grantee";
DROP ROLE IF EXISTS dcl_04995_grantor;
DROP ROLE IF EXISTS dcl_04995_member;
CREATE ROLE "dcl_04995_Grantee";
CREATE ROLE dcl_04995_grantor;
CREATE ROLE dcl_04995_member;
DROP SCHEMA IF EXISTS dcl_04995_schema CASCADE;
CREATE SCHEMA dcl_04995_schema;
GRANT USAGE ON SCHEMA dcl_04995_schema TO dcl_04995_grantor WITH GRANT OPTION;
SET ROLE dcl_04995_grantor;
GRANT USAGE ON SCHEMA dcl_04995_schema TO CURRENT_ROLE GRANTED BY dcl_04995_grantor;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'schema_database_tablespace' AS privilege_scope;
DROP SCHEMA IF EXISTS dcl_04995_schema CASCADE;
DROP OWNED BY "dcl_04995_Grantee";
DROP OWNED BY dcl_04995_member;
DROP OWNED BY dcl_04995_grantor;
DROP ROLE IF EXISTS dcl_04995_member;
DROP ROLE IF EXISTS dcl_04995_grantor;
DROP ROLE IF EXISTS "dcl_04995_Grantee";
