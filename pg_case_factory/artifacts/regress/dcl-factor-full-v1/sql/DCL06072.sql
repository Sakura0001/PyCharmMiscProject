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
-- factor grantee_shape=current_user
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=quoted_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=effect_query
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_06072_Grantee";
DROP ROLE IF EXISTS dcl_06072_grantor;
DROP ROLE IF EXISTS dcl_06072_member;
CREATE ROLE "dcl_06072_Grantee";
CREATE ROLE dcl_06072_grantor;
CREATE ROLE dcl_06072_member;
DROP TYPE IF EXISTS dcl_06072_type;
CREATE TYPE dcl_06072_type AS ENUM ('alpha', 'beta');
SET ROLE "dcl_06072_Grantee";
GRANT USAGE ON TYPE dcl_06072_missing_object TO CURRENT_USER WITH GRANT OPTION GRANTED BY dcl_06072_grantor;
RESET ROLE;
SELECT true AS privilege_effect_observed;
DROP TYPE IF EXISTS dcl_06072_type;
DROP OWNED BY "dcl_06072_Grantee";
DROP OWNED BY dcl_06072_member;
DROP OWNED BY dcl_06072_grantor;
DROP ROLE IF EXISTS dcl_06072_member;
DROP ROLE IF EXISTS dcl_06072_grantor;
DROP ROLE IF EXISTS "dcl_06072_Grantee";
