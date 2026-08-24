-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_3 (sequence) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_3
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
-- factor grantee_shape=public
-- factor grant_option_shape=admin_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=missing_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_01039_grantor;
DROP ROLE IF EXISTS dcl_01039_member;
CREATE ROLE dcl_01039_grantor;
CREATE ROLE dcl_01039_member;
DROP SCHEMA IF EXISTS dcl_01039_schema CASCADE;
CREATE SCHEMA dcl_01039_schema;
CREATE SEQUENCE dcl_01039_schema.dcl_01039_sequence;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA dcl_01039_missing_object TO dcl_01039_grantor WITH GRANT OPTION;
GRANT dcl_01039_grantor TO dcl_01039_member WITH SET TRUE;
SET ROLE dcl_01039_member;
SET ROLE dcl_01039_grantor;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA dcl_01039_missing_object TO PUBLIC WITH ADMIN OPTION;
RESET ROLE;
SELECT has_sequence_privilege(CURRENT_USER, 'dcl_01039_sequence', 'USAGE');
RESET ROLE;
RESET ALL;
DROP SCHEMA IF EXISTS dcl_01039_schema CASCADE;
DROP OWNED BY dcl_01039_member;
DROP OWNED BY dcl_01039_grantor;
DROP ROLE IF EXISTS dcl_01039_member;
DROP ROLE IF EXISTS dcl_01039_grantor;
