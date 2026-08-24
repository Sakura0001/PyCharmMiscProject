-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_3 (sequence) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_3
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=session_user
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_07979_grantee;
DROP ROLE IF EXISTS dcl_07979_grantor;
DROP ROLE IF EXISTS dcl_07979_member;
CREATE ROLE dcl_07979_grantee;
CREATE ROLE dcl_07979_grantor;
CREATE ROLE dcl_07979_member;
DROP SCHEMA IF EXISTS dcl_07979_schema CASCADE;
CREATE SCHEMA dcl_07979_schema;
CREATE SEQUENCE dcl_07979_schema.dcl_07979_sequence;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA dcl_07979_missing_object TO SESSION_USER;
BEGIN;
SET ROLE dcl_07979_grantee;
REVOKE GRANT OPTION FOR USAGE ON ALL SEQUENCES IN SCHEMA dcl_07979_missing_object FROM SESSION_USER GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT has_sequence_privilege(CURRENT_USER, 'dcl_07979_sequence', 'USAGE');
ROLLBACK;
DROP SCHEMA IF EXISTS dcl_07979_schema CASCADE;
DROP OWNED BY dcl_07979_grantee;
DROP OWNED BY dcl_07979_member;
DROP OWNED BY dcl_07979_grantor;
DROP ROLE IF EXISTS dcl_07979_member;
DROP ROLE IF EXISTS dcl_07979_grantor;
DROP ROLE IF EXISTS dcl_07979_grantee;
