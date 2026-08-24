-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_14 (type) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=current_role
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
DROP ROLE IF EXISTS "dcl_06180_Grantee";
DROP ROLE IF EXISTS dcl_06180_grantor;
DROP ROLE IF EXISTS dcl_06180_member;
CREATE ROLE "dcl_06180_Grantee";
CREATE ROLE dcl_06180_grantor;
CREATE ROLE dcl_06180_member;
DROP TYPE IF EXISTS dcl_06180_type;
CREATE TYPE dcl_06180_type AS ENUM ('alpha', 'beta');
SET ROLE "dcl_06180_Grantee";
GRANT USAGE ON TYPE dcl_06180_missing_object TO CURRENT_ROLE WITH GRANT OPTION GRANTED BY dcl_06180_grantor;
RESET ROLE;
SELECT true AS privilege_effect_observed;
DROP TYPE IF EXISTS dcl_06180_type;
DROP OWNED BY "dcl_06180_Grantee";
DROP OWNED BY dcl_06180_member;
DROP OWNED BY dcl_06180_grantor;
DROP ROLE IF EXISTS dcl_06180_member;
DROP ROLE IF EXISTS dcl_06180_grantor;
DROP ROLE IF EXISTS "dcl_06180_Grantee";
