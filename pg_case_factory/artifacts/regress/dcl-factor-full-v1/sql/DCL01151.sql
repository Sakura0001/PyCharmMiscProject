-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_3 (sequence) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_3
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=role_name
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
DROP ROLE IF EXISTS dcl_01151_grantee;
DROP ROLE IF EXISTS dcl_01151_grantor;
DROP ROLE IF EXISTS dcl_01151_member;
CREATE ROLE dcl_01151_grantee;
CREATE ROLE dcl_01151_grantor;
CREATE ROLE dcl_01151_member;
DROP SCHEMA IF EXISTS dcl_01151_schema CASCADE;
CREATE SCHEMA dcl_01151_schema;
CREATE SEQUENCE dcl_01151_schema.dcl_01151_sequence;
BEGIN;
SET ROLE dcl_01151_grantee;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA dcl_01151_missing_object TO dcl_01151_grantee WITH INHERIT TRUE GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT has_sequence_privilege(CURRENT_USER, 'dcl_01151_sequence', 'USAGE');
ROLLBACK;
DROP SCHEMA IF EXISTS dcl_01151_schema CASCADE;
DROP OWNED BY dcl_01151_grantee;
DROP OWNED BY dcl_01151_member;
DROP OWNED BY dcl_01151_grantor;
DROP ROLE IF EXISTS dcl_01151_member;
DROP ROLE IF EXISTS dcl_01151_grantor;
DROP ROLE IF EXISTS dcl_01151_grantee;
