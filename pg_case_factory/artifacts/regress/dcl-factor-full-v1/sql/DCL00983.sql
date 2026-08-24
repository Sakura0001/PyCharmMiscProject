-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_3 (sequence) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_3
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=public
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_00983_grantee;
DROP ROLE IF EXISTS dcl_00983_grantor;
DROP ROLE IF EXISTS dcl_00983_member;
CREATE ROLE dcl_00983_grantee;
CREATE ROLE dcl_00983_grantor;
CREATE ROLE dcl_00983_member;
DROP SCHEMA IF EXISTS dcl_00983_schema CASCADE;
CREATE SCHEMA dcl_00983_schema;
CREATE SEQUENCE dcl_00983_schema.dcl_00983_sequence;
BEGIN;
SET ROLE dcl_00983_grantee;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA dcl_00983_missing_object TO PUBLIC WITH INHERIT TRUE GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT has_sequence_privilege(CURRENT_USER, 'dcl_00983_sequence', 'USAGE');
ROLLBACK;
DROP SCHEMA IF EXISTS dcl_00983_schema CASCADE;
DROP OWNED BY dcl_00983_grantee;
DROP OWNED BY dcl_00983_member;
DROP OWNED BY dcl_00983_grantor;
DROP ROLE IF EXISTS dcl_00983_member;
DROP ROLE IF EXISTS dcl_00983_grantor;
DROP ROLE IF EXISTS dcl_00983_grantee;
