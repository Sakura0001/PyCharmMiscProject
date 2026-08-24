-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_3 (sequence) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_3
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
DROP ROLE IF EXISTS "dcl_08112_Grantee";
DROP ROLE IF EXISTS dcl_08112_grantor;
DROP ROLE IF EXISTS dcl_08112_member;
CREATE ROLE "dcl_08112_Grantee";
CREATE ROLE dcl_08112_grantor;
CREATE ROLE dcl_08112_member;
DROP SEQUENCE IF EXISTS dcl_08112_sequence;
CREATE SEQUENCE dcl_08112_sequence;
GRANT USAGE ON SEQUENCE dcl_08112_missing_object TO "dcl_08112_Grantee";
SET ROLE "dcl_08112_Grantee";
REVOKE GRANT OPTION FOR USAGE ON SEQUENCE dcl_08112_missing_object FROM "dcl_08112_Grantee" GRANTED BY dcl_08112_grantor RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
DROP SEQUENCE IF EXISTS dcl_08112_sequence;
DROP OWNED BY "dcl_08112_Grantee";
DROP OWNED BY dcl_08112_member;
DROP OWNED BY dcl_08112_grantor;
DROP ROLE IF EXISTS dcl_08112_member;
DROP ROLE IF EXISTS dcl_08112_grantor;
DROP ROLE IF EXISTS "dcl_08112_Grantee";
