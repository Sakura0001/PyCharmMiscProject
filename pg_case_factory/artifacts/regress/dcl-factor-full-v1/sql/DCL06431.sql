-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_15 (role_membership) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_15
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
-- factor grantee_shape=role_name
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
DROP ROLE IF EXISTS dcl_06431_grantee;
DROP ROLE IF EXISTS dcl_06431_grantor;
DROP ROLE IF EXISTS dcl_06431_member;
CREATE ROLE dcl_06431_grantee;
CREATE ROLE dcl_06431_grantor;
CREATE ROLE dcl_06431_member;
BEGIN;
SET ROLE dcl_06431_grantee;
GRANT dcl_06431_missing_member TO dcl_06431_grantee WITH GRANT OPTION GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT true AS role_membership_statement_completed;
ROLLBACK;
DROP OWNED BY dcl_06431_grantee;
DROP OWNED BY dcl_06431_member;
DROP OWNED BY dcl_06431_grantor;
DROP ROLE IF EXISTS dcl_06431_member;
DROP ROLE IF EXISTS dcl_06431_grantor;
DROP ROLE IF EXISTS dcl_06431_grantee;
