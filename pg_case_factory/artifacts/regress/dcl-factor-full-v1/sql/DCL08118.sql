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
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=quoted_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=error_assertion
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_08118_Grantee";
DROP ROLE IF EXISTS dcl_08118_grantor;
DROP ROLE IF EXISTS dcl_08118_member;
CREATE ROLE "dcl_08118_Grantee";
CREATE ROLE dcl_08118_grantor;
CREATE ROLE dcl_08118_member;
DROP SEQUENCE IF EXISTS dcl_08118_sequence;
CREATE SEQUENCE dcl_08118_sequence;
GRANT USAGE ON SEQUENCE dcl_08118_missing_object TO "dcl_08118_Grantee";
SET ROLE "dcl_08118_Grantee";
REVOKE INHERIT OPTION FOR USAGE ON SEQUENCE dcl_08118_missing_object FROM "dcl_08118_Grantee" GRANTED BY dcl_08118_grantor RESTRICT;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
DROP SEQUENCE IF EXISTS dcl_08118_sequence;
DROP OWNED BY "dcl_08118_Grantee";
DROP OWNED BY dcl_08118_member;
DROP OWNED BY dcl_08118_grantor;
DROP ROLE IF EXISTS dcl_08118_member;
DROP ROLE IF EXISTS dcl_08118_grantor;
DROP ROLE IF EXISTS "dcl_08118_Grantee";
