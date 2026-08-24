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
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=missing_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_07987_grantor;
DROP ROLE IF EXISTS dcl_07987_member;
CREATE ROLE dcl_07987_grantor;
CREATE ROLE dcl_07987_member;
DROP SCHEMA IF EXISTS dcl_07987_schema CASCADE;
CREATE SCHEMA dcl_07987_schema;
CREATE SEQUENCE dcl_07987_schema.dcl_07987_sequence;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA dcl_07987_missing_object TO dcl_07987_missing_role;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA dcl_07987_missing_object TO dcl_07987_grantor WITH GRANT OPTION;
GRANT dcl_07987_grantor TO dcl_07987_member WITH SET TRUE;
SET ROLE dcl_07987_member;
SET ROLE dcl_07987_grantor;
REVOKE USAGE ON ALL SEQUENCES IN SCHEMA dcl_07987_missing_object FROM dcl_07987_missing_role RESTRICT;
RESET ROLE;
SELECT has_sequence_privilege(CURRENT_USER, 'dcl_07987_sequence', 'USAGE');
RESET ROLE;
RESET ALL;
DROP SCHEMA IF EXISTS dcl_07987_schema CASCADE;
DROP OWNED BY dcl_07987_member;
DROP OWNED BY dcl_07987_grantor;
DROP ROLE IF EXISTS dcl_07987_member;
DROP ROLE IF EXISTS dcl_07987_grantor;
