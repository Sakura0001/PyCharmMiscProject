-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_3 (sequence) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_3
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=session_user
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_01311_Grantee";
DROP ROLE IF EXISTS dcl_01311_grantor;
DROP ROLE IF EXISTS dcl_01311_member;
CREATE ROLE "dcl_01311_Grantee";
CREATE ROLE dcl_01311_grantor;
CREATE ROLE dcl_01311_member;
DROP SCHEMA IF EXISTS dcl_01311_schema CASCADE;
CREATE SCHEMA dcl_01311_schema;
CREATE SEQUENCE dcl_01311_schema.dcl_01311_sequence;
SET ROLE "dcl_01311_Grantee";
GRANT USAGE ON ALL SEQUENCES IN SCHEMA dcl_01311_missing_object TO SESSION_USER GRANTED BY dcl_01311_grantor;
RESET ROLE;
SELECT has_sequence_privilege(CURRENT_USER, 'dcl_01311_sequence', 'USAGE');
DROP SCHEMA IF EXISTS dcl_01311_schema CASCADE;
DROP OWNED BY "dcl_01311_Grantee";
DROP OWNED BY dcl_01311_member;
DROP OWNED BY dcl_01311_grantor;
DROP ROLE IF EXISTS dcl_01311_member;
DROP ROLE IF EXISTS dcl_01311_grantor;
DROP ROLE IF EXISTS "dcl_01311_Grantee";
