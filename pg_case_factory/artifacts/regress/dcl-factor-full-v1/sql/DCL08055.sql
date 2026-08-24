-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_3 (sequence) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_3
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
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
DROP ROLE IF EXISTS "dcl_08055_Grantee";
DROP ROLE IF EXISTS dcl_08055_grantor;
DROP ROLE IF EXISTS dcl_08055_member;
CREATE ROLE "dcl_08055_Grantee";
CREATE ROLE dcl_08055_grantor;
CREATE ROLE dcl_08055_member;
DROP SCHEMA IF EXISTS dcl_08055_schema CASCADE;
CREATE SCHEMA dcl_08055_schema;
CREATE SEQUENCE dcl_08055_schema.dcl_08055_sequence;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA dcl_08055_missing_object TO "dcl_08055_Grantee";
SET ROLE "dcl_08055_Grantee";
REVOKE ADMIN OPTION FOR USAGE ON ALL SEQUENCES IN SCHEMA dcl_08055_missing_object FROM "dcl_08055_Grantee" GRANTED BY dcl_08055_grantor RESTRICT;
RESET ROLE;
SELECT has_sequence_privilege(CURRENT_USER, 'dcl_08055_sequence', 'USAGE');
DROP SCHEMA IF EXISTS dcl_08055_schema CASCADE;
DROP OWNED BY "dcl_08055_Grantee";
DROP OWNED BY dcl_08055_member;
DROP OWNED BY dcl_08055_grantor;
DROP ROLE IF EXISTS dcl_08055_member;
DROP ROLE IF EXISTS dcl_08055_grantor;
DROP ROLE IF EXISTS "dcl_08055_Grantee";
