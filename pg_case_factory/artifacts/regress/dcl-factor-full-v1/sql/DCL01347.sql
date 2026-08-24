-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_3 (sequence) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_3
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
-- factor grantee_shape=current_role
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
DROP ROLE IF EXISTS "dcl_01347_Grantee";
DROP ROLE IF EXISTS dcl_01347_grantor;
DROP ROLE IF EXISTS dcl_01347_member;
CREATE ROLE "dcl_01347_Grantee";
CREATE ROLE dcl_01347_grantor;
CREATE ROLE dcl_01347_member;
DROP SCHEMA IF EXISTS dcl_01347_schema CASCADE;
CREATE SCHEMA dcl_01347_schema;
CREATE SEQUENCE dcl_01347_schema.dcl_01347_sequence;
SET ROLE "dcl_01347_Grantee";
GRANT USAGE ON ALL SEQUENCES IN SCHEMA dcl_01347_missing_object TO CURRENT_ROLE GRANTED BY dcl_01347_grantor;
RESET ROLE;
SELECT has_sequence_privilege(CURRENT_USER, 'dcl_01347_sequence', 'USAGE');
DROP SCHEMA IF EXISTS dcl_01347_schema CASCADE;
DROP OWNED BY "dcl_01347_Grantee";
DROP OWNED BY dcl_01347_member;
DROP OWNED BY dcl_01347_grantor;
DROP ROLE IF EXISTS dcl_01347_member;
DROP ROLE IF EXISTS dcl_01347_grantor;
DROP ROLE IF EXISTS "dcl_01347_Grantee";
