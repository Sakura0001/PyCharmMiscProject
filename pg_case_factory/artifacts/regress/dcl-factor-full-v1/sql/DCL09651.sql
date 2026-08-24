-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_7 (foreign_server) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_7
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
-- factor grantee_shape=current_user
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
DROP ROLE IF EXISTS "dcl_09651_Grantee";
DROP ROLE IF EXISTS dcl_09651_grantor;
DROP ROLE IF EXISTS dcl_09651_member;
CREATE ROLE "dcl_09651_Grantee";
CREATE ROLE dcl_09651_grantor;
CREATE ROLE dcl_09651_member;
DROP SERVER IF EXISTS dcl_09651_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09651_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_09651_fdw;
CREATE SERVER dcl_09651_server FOREIGN DATA WRAPPER dcl_09651_fdw;
GRANT USAGE ON FOREIGN SERVER dcl_09651_missing_object TO CURRENT_USER;
SET ROLE "dcl_09651_Grantee";
REVOKE ADMIN OPTION FOR USAGE ON FOREIGN SERVER dcl_09651_missing_object FROM CURRENT_USER GRANTED BY dcl_09651_grantor RESTRICT;
RESET ROLE;
SELECT true AS foreign_server_privilege_statement_completed;
DROP SERVER IF EXISTS dcl_09651_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09651_fdw CASCADE;
DROP OWNED BY "dcl_09651_Grantee";
DROP OWNED BY dcl_09651_member;
DROP OWNED BY dcl_09651_grantor;
DROP ROLE IF EXISTS dcl_09651_member;
DROP ROLE IF EXISTS dcl_09651_grantor;
DROP ROLE IF EXISTS "dcl_09651_Grantee";
