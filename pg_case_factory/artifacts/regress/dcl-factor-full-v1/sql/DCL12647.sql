-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_13 (tablespace) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_13
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
-- factor grantee_shape=current_user
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
DROP ROLE IF EXISTS dcl_12647_grantee;
DROP ROLE IF EXISTS dcl_12647_grantor;
DROP ROLE IF EXISTS dcl_12647_member;
CREATE ROLE dcl_12647_grantee;
CREATE ROLE dcl_12647_grantor;
CREATE ROLE dcl_12647_member;
GRANT CREATE ON TABLESPACE dcl_12647_missing_object TO CURRENT_USER;
BEGIN;
SET ROLE dcl_12647_grantee;
REVOKE GRANT OPTION FOR CREATE ON TABLESPACE dcl_12647_missing_object FROM CURRENT_USER GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT has_tablespace_privilege(CURRENT_USER, 'dcl_12647_tablespace', 'CREATE');
ROLLBACK;
DROP OWNED BY dcl_12647_grantee;
DROP OWNED BY dcl_12647_member;
DROP OWNED BY dcl_12647_grantor;
DROP ROLE IF EXISTS dcl_12647_member;
DROP ROLE IF EXISTS dcl_12647_grantor;
DROP ROLE IF EXISTS dcl_12647_grantee;
