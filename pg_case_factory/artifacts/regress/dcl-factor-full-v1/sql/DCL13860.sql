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
-- factor expected_status=success
-- factor privilege_scope=table_privilege
-- factor grantee_shape=role_name
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=none
-- factor ownership_boundary=owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS dcl_13860_grantee;
DROP ROLE IF EXISTS dcl_13860_grantor;
DROP ROLE IF EXISTS dcl_13860_member;
CREATE ROLE dcl_13860_grantee;
CREATE ROLE dcl_13860_grantor;
CREATE ROLE dcl_13860_member;
DROP SERVER IF EXISTS dcl_13860_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_13860_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_13860_fdw;
CREATE SERVER dcl_13860_server FOREIGN DATA WRAPPER dcl_13860_fdw;
GRANT USAGE ON FOREIGN SERVER dcl_13860_server TO dcl_13860_grantee;
REVOKE USAGE ON FOREIGN SERVER dcl_13860_server FROM dcl_13860_grantee RESTRICT;
SELECT true AS foreign_server_privilege_statement_completed;
DROP SERVER IF EXISTS dcl_13860_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_13860_fdw CASCADE;
DROP OWNED BY dcl_13860_grantee;
DROP OWNED BY dcl_13860_member;
DROP OWNED BY dcl_13860_grantor;
DROP ROLE IF EXISTS dcl_13860_member;
DROP ROLE IF EXISTS dcl_13860_grantor;
DROP ROLE IF EXISTS dcl_13860_grantee;
