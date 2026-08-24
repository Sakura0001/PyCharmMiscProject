-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_14 (type) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
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
DROP ROLE IF EXISTS dcl_06143_grantee;
DROP ROLE IF EXISTS dcl_06143_grantor;
DROP ROLE IF EXISTS dcl_06143_member;
CREATE ROLE dcl_06143_grantee;
CREATE ROLE dcl_06143_grantor;
CREATE ROLE dcl_06143_member;
DROP TYPE IF EXISTS dcl_06143_type;
CREATE TYPE dcl_06143_type AS ENUM ('alpha', 'beta');
BEGIN;
SET ROLE dcl_06143_grantee;
GRANT USAGE ON TYPE dcl_06143_missing_object TO SESSION_USER WITH GRANT OPTION GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT has_type_privilege(CURRENT_USER, 'dcl_06143_type', 'USAGE');
ROLLBACK;
DROP TYPE IF EXISTS dcl_06143_type;
DROP OWNED BY dcl_06143_grantee;
DROP OWNED BY dcl_06143_member;
DROP OWNED BY dcl_06143_grantor;
DROP ROLE IF EXISTS dcl_06143_member;
DROP ROLE IF EXISTS dcl_06143_grantor;
DROP ROLE IF EXISTS dcl_06143_grantee;
