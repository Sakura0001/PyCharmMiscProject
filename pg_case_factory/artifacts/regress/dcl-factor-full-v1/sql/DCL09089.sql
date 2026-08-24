-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_6 (foreign_data_wrapper) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_6
-- factor expected_status=success
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=current_user
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=member_role
-- factor verification_mode=effect_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS "dcl_09089_Grantee";
DROP ROLE IF EXISTS dcl_09089_grantor;
DROP ROLE IF EXISTS dcl_09089_member;
CREATE ROLE "dcl_09089_Grantee";
CREATE ROLE dcl_09089_grantor;
CREATE ROLE dcl_09089_member;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09089_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_09089_fdw;
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_09089_fdw TO CURRENT_USER;
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_09089_fdw TO dcl_09089_grantor WITH GRANT OPTION;
BEGIN;
SET ROLE dcl_09089_grantor;
REVOKE GRANT OPTION FOR USAGE ON FOREIGN DATA WRAPPER dcl_09089_fdw FROM CURRENT_USER GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT true AS privilege_effect_observed;
ROLLBACK;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09089_fdw CASCADE;
DROP OWNED BY "dcl_09089_Grantee";
DROP OWNED BY dcl_09089_member;
DROP OWNED BY dcl_09089_grantor;
DROP ROLE IF EXISTS dcl_09089_member;
DROP ROLE IF EXISTS dcl_09089_grantor;
DROP ROLE IF EXISTS "dcl_09089_Grantee";
