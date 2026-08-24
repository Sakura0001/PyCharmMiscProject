-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_12 (schema) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_12
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=public
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=returned_rows
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_05265_Grantee";
DROP ROLE IF EXISTS dcl_05265_grantor;
DROP ROLE IF EXISTS dcl_05265_member;
CREATE ROLE "dcl_05265_Grantee";
CREATE ROLE dcl_05265_grantor;
CREATE ROLE dcl_05265_member;
DROP SCHEMA IF EXISTS dcl_05265_schema CASCADE;
CREATE SCHEMA dcl_05265_schema;
SET ROLE "dcl_05265_Grantee";
GRANT USAGE ON SCHEMA dcl_05265_missing_object TO PUBLIC GRANTED BY dcl_05265_grantor;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'role_membership' AS privilege_scope;
DROP SCHEMA IF EXISTS dcl_05265_schema CASCADE;
DROP OWNED BY "dcl_05265_Grantee";
DROP OWNED BY dcl_05265_member;
DROP OWNED BY dcl_05265_grantor;
DROP ROLE IF EXISTS dcl_05265_member;
DROP ROLE IF EXISTS dcl_05265_grantor;
DROP ROLE IF EXISTS "dcl_05265_Grantee";
