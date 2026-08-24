-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_7 (foreign_server) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_7
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=session_user
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=missing_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_09595_grantor;
DROP ROLE IF EXISTS dcl_09595_member;
CREATE ROLE dcl_09595_grantor;
CREATE ROLE dcl_09595_member;
DROP SERVER IF EXISTS dcl_09595_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09595_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_09595_fdw;
CREATE SERVER dcl_09595_server FOREIGN DATA WRAPPER dcl_09595_fdw;
GRANT USAGE ON FOREIGN SERVER dcl_09595_missing_object TO SESSION_USER;
GRANT USAGE ON FOREIGN SERVER dcl_09595_missing_object TO dcl_09595_grantor WITH GRANT OPTION;
GRANT dcl_09595_grantor TO dcl_09595_member WITH SET TRUE;
SET ROLE dcl_09595_member;
SET ROLE dcl_09595_grantor;
REVOKE USAGE ON FOREIGN SERVER dcl_09595_missing_object FROM SESSION_USER RESTRICT;
RESET ROLE;
SELECT true AS foreign_server_privilege_statement_completed;
RESET ROLE;
RESET ALL;
DROP SERVER IF EXISTS dcl_09595_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09595_fdw CASCADE;
DROP OWNED BY dcl_09595_member;
DROP OWNED BY dcl_09595_grantor;
DROP ROLE IF EXISTS dcl_09595_member;
DROP ROLE IF EXISTS dcl_09595_grantor;
