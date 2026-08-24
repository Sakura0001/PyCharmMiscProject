-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_6 (foreign_data_wrapper) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_6
-- factor expected_status=failure
-- factor privilege_scope=role_membership
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
DROP ROLE IF EXISTS dcl_09359_grantee;
DROP ROLE IF EXISTS dcl_09359_grantor;
DROP ROLE IF EXISTS dcl_09359_member;
CREATE ROLE dcl_09359_grantee;
CREATE ROLE dcl_09359_grantor;
CREATE ROLE dcl_09359_member;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09359_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_09359_fdw;
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_09359_missing_object TO PUBLIC;
BEGIN;
SET ROLE dcl_09359_grantee;
REVOKE INHERIT OPTION FOR USAGE ON FOREIGN DATA WRAPPER dcl_09359_missing_object FROM PUBLIC GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT true AS fdw_privilege_statement_completed;
ROLLBACK;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09359_fdw CASCADE;
DROP OWNED BY dcl_09359_grantee;
DROP OWNED BY dcl_09359_member;
DROP OWNED BY dcl_09359_grantor;
DROP ROLE IF EXISTS dcl_09359_member;
DROP ROLE IF EXISTS dcl_09359_grantor;
DROP ROLE IF EXISTS dcl_09359_grantee;
