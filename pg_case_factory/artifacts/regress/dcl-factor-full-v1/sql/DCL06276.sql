-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_14 (type) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
-- factor grantee_shape=role_name
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
DROP ROLE IF EXISTS "dcl_06276_Grantee";
DROP ROLE IF EXISTS dcl_06276_grantor;
DROP ROLE IF EXISTS dcl_06276_member;
CREATE ROLE "dcl_06276_Grantee";
CREATE ROLE dcl_06276_grantor;
CREATE ROLE dcl_06276_member;
DROP TYPE IF EXISTS dcl_06276_type;
CREATE TYPE dcl_06276_type AS ENUM ('alpha', 'beta');
SET ROLE "dcl_06276_Grantee";
GRANT USAGE ON TYPE dcl_06276_missing_object TO "dcl_06276_Grantee" WITH GRANT OPTION GRANTED BY dcl_06276_grantor;
RESET ROLE;
SELECT true AS privilege_effect_observed;
DROP TYPE IF EXISTS dcl_06276_type;
DROP OWNED BY "dcl_06276_Grantee";
DROP OWNED BY dcl_06276_member;
DROP OWNED BY dcl_06276_grantor;
DROP ROLE IF EXISTS dcl_06276_member;
DROP ROLE IF EXISTS dcl_06276_grantor;
DROP ROLE IF EXISTS "dcl_06276_Grantee";
