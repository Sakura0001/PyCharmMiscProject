-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_14 (type) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
-- factor grantee_shape=current_user
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
DROP ROLE IF EXISTS "dcl_06009_Grantee";
DROP ROLE IF EXISTS dcl_06009_grantor;
DROP ROLE IF EXISTS dcl_06009_member;
CREATE ROLE "dcl_06009_Grantee";
CREATE ROLE dcl_06009_grantor;
CREATE ROLE dcl_06009_member;
DROP TYPE IF EXISTS dcl_06009_type;
CREATE TYPE dcl_06009_type AS ENUM ('alpha', 'beta');
SET ROLE "dcl_06009_Grantee";
GRANT USAGE ON TYPE dcl_06009_missing_object TO CURRENT_USER GRANTED BY dcl_06009_grantor;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'column_privilege' AS privilege_scope;
DROP TYPE IF EXISTS dcl_06009_type;
DROP OWNED BY "dcl_06009_Grantee";
DROP OWNED BY dcl_06009_member;
DROP OWNED BY dcl_06009_grantor;
DROP ROLE IF EXISTS dcl_06009_member;
DROP ROLE IF EXISTS dcl_06009_grantor;
DROP ROLE IF EXISTS "dcl_06009_Grantee";
