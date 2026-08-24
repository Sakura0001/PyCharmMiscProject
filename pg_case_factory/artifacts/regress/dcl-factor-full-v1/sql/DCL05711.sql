-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_13 (tablespace) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_13
-- factor expected_status=failure
-- factor privilege_scope=role_membership
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
DROP ROLE IF EXISTS dcl_05711_grantee;
DROP ROLE IF EXISTS dcl_05711_grantor;
DROP ROLE IF EXISTS dcl_05711_member;
CREATE ROLE dcl_05711_grantee;
CREATE ROLE dcl_05711_grantor;
CREATE ROLE dcl_05711_member;
BEGIN;
SET ROLE dcl_05711_grantee;
GRANT CREATE ON TABLESPACE dcl_05711_missing_object TO dcl_05711_grantee WITH INHERIT TRUE GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT has_tablespace_privilege(CURRENT_USER, 'dcl_05711_tablespace', 'CREATE');
ROLLBACK;
DROP OWNED BY dcl_05711_grantee;
DROP OWNED BY dcl_05711_member;
DROP OWNED BY dcl_05711_grantor;
DROP ROLE IF EXISTS dcl_05711_member;
DROP ROLE IF EXISTS dcl_05711_grantor;
DROP ROLE IF EXISTS dcl_05711_grantee;
