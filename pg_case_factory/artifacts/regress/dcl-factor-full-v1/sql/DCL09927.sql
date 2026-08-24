-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_7 (foreign_server) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_7
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
-- factor grantee_shape=public
-- factor grant_option_shape=admin_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_09927_Grantee";
DROP ROLE IF EXISTS dcl_09927_grantor;
DROP ROLE IF EXISTS dcl_09927_member;
CREATE ROLE "dcl_09927_Grantee";
CREATE ROLE dcl_09927_grantor;
CREATE ROLE dcl_09927_member;
DROP SERVER IF EXISTS dcl_09927_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09927_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_09927_fdw;
CREATE SERVER dcl_09927_server FOREIGN DATA WRAPPER dcl_09927_fdw;
GRANT USAGE ON FOREIGN SERVER dcl_09927_missing_object TO PUBLIC;
SET ROLE "dcl_09927_Grantee";
REVOKE ADMIN OPTION FOR USAGE ON FOREIGN SERVER dcl_09927_missing_object FROM PUBLIC GRANTED BY dcl_09927_grantor RESTRICT;
RESET ROLE;
SELECT true AS foreign_server_privilege_statement_completed;
DROP SERVER IF EXISTS dcl_09927_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09927_fdw CASCADE;
DROP OWNED BY "dcl_09927_Grantee";
DROP OWNED BY dcl_09927_member;
DROP OWNED BY dcl_09927_grantor;
DROP ROLE IF EXISTS dcl_09927_member;
DROP ROLE IF EXISTS dcl_09927_grantor;
DROP ROLE IF EXISTS "dcl_09927_Grantee";
