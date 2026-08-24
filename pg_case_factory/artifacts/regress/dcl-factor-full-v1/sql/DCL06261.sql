-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_14 (type) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=session_user
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
DROP ROLE IF EXISTS "dcl_06261_Grantee";
DROP ROLE IF EXISTS dcl_06261_grantor;
DROP ROLE IF EXISTS dcl_06261_member;
CREATE ROLE "dcl_06261_Grantee";
CREATE ROLE dcl_06261_grantor;
CREATE ROLE dcl_06261_member;
DROP TYPE IF EXISTS dcl_06261_type;
CREATE TYPE dcl_06261_type AS ENUM ('alpha', 'beta');
SET ROLE "dcl_06261_Grantee";
GRANT USAGE ON TYPE dcl_06261_missing_object TO SESSION_USER GRANTED BY dcl_06261_grantor;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'parameter_privilege' AS privilege_scope;
DROP TYPE IF EXISTS dcl_06261_type;
DROP OWNED BY "dcl_06261_Grantee";
DROP OWNED BY dcl_06261_member;
DROP OWNED BY dcl_06261_grantor;
DROP ROLE IF EXISTS dcl_06261_member;
DROP ROLE IF EXISTS dcl_06261_grantor;
DROP ROLE IF EXISTS "dcl_06261_Grantee";
