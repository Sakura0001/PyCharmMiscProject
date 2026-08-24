-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_13 (tablespace) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_13
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
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
DROP ROLE IF EXISTS dcl_05663_grantee;
DROP ROLE IF EXISTS dcl_05663_grantor;
DROP ROLE IF EXISTS dcl_05663_member;
CREATE ROLE dcl_05663_grantee;
CREATE ROLE dcl_05663_grantor;
CREATE ROLE dcl_05663_member;
BEGIN;
SET ROLE dcl_05663_grantee;
GRANT CREATE ON TABLESPACE dcl_05663_missing_object TO PUBLIC WITH INHERIT TRUE GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT has_tablespace_privilege(CURRENT_USER, 'dcl_05663_tablespace', 'CREATE');
ROLLBACK;
DROP OWNED BY dcl_05663_grantee;
DROP OWNED BY dcl_05663_member;
DROP OWNED BY dcl_05663_grantor;
DROP ROLE IF EXISTS dcl_05663_member;
DROP ROLE IF EXISTS dcl_05663_grantor;
DROP ROLE IF EXISTS dcl_05663_grantee;
