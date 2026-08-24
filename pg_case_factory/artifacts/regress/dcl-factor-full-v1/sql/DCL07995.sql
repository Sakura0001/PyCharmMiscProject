-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_3 (sequence) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_3
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=role_name
-- factor grant_option_shape=admin_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_07995_Grantee";
DROP ROLE IF EXISTS dcl_07995_grantor;
DROP ROLE IF EXISTS dcl_07995_member;
CREATE ROLE "dcl_07995_Grantee";
CREATE ROLE dcl_07995_grantor;
CREATE ROLE dcl_07995_member;
DROP SCHEMA IF EXISTS dcl_07995_schema CASCADE;
CREATE SCHEMA dcl_07995_schema;
CREATE SEQUENCE dcl_07995_schema.dcl_07995_sequence;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA dcl_07995_missing_object TO "dcl_07995_Grantee";
SET ROLE "dcl_07995_Grantee";
REVOKE ADMIN OPTION FOR USAGE ON ALL SEQUENCES IN SCHEMA dcl_07995_missing_object FROM "dcl_07995_Grantee" GRANTED BY dcl_07995_grantor RESTRICT;
RESET ROLE;
SELECT has_sequence_privilege(CURRENT_USER, 'dcl_07995_sequence', 'USAGE');
DROP SCHEMA IF EXISTS dcl_07995_schema CASCADE;
DROP OWNED BY "dcl_07995_Grantee";
DROP OWNED BY dcl_07995_member;
DROP OWNED BY dcl_07995_grantor;
DROP ROLE IF EXISTS dcl_07995_member;
DROP ROLE IF EXISTS dcl_07995_grantor;
DROP ROLE IF EXISTS "dcl_07995_Grantee";
