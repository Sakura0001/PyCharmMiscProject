-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_14 (type) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
-- factor expected_status=success
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=session_user
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=member_role
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS "dcl_12691_Grantee";
DROP ROLE IF EXISTS dcl_12691_grantor;
DROP ROLE IF EXISTS dcl_12691_member;
CREATE ROLE "dcl_12691_Grantee";
CREATE ROLE dcl_12691_grantor;
CREATE ROLE dcl_12691_member;
DROP TYPE IF EXISTS dcl_12691_type;
CREATE TYPE dcl_12691_type AS ENUM ('alpha', 'beta');
GRANT USAGE ON TYPE dcl_12691_type TO SESSION_USER;
GRANT USAGE ON TYPE dcl_12691_type TO dcl_12691_grantor WITH GRANT OPTION;
SET ROLE dcl_12691_grantor;
REVOKE USAGE ON TYPE dcl_12691_type FROM SESSION_USER RESTRICT;
RESET ROLE;
SELECT has_type_privilege(CURRENT_USER, 'dcl_12691_type', 'USAGE');
RESET ROLE;
RESET ALL;
DROP TYPE IF EXISTS dcl_12691_type;
DROP OWNED BY "dcl_12691_Grantee";
DROP OWNED BY dcl_12691_member;
DROP OWNED BY dcl_12691_grantor;
DROP ROLE IF EXISTS dcl_12691_member;
DROP ROLE IF EXISTS dcl_12691_grantor;
DROP ROLE IF EXISTS "dcl_12691_Grantee";
