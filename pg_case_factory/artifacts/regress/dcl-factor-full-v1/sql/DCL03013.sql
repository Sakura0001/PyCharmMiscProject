-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_7 (foreign_server) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_7
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=public
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=missing_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=returned_rows
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_03013_grantor;
DROP ROLE IF EXISTS dcl_03013_member;
CREATE ROLE dcl_03013_grantor;
CREATE ROLE dcl_03013_member;
DROP SERVER IF EXISTS dcl_03013_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_03013_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_03013_fdw;
CREATE SERVER dcl_03013_server FOREIGN DATA WRAPPER dcl_03013_fdw;
GRANT USAGE ON FOREIGN SERVER dcl_03013_missing_object TO dcl_03013_grantor WITH GRANT OPTION;
GRANT dcl_03013_grantor TO dcl_03013_member WITH SET TRUE;
SET ROLE dcl_03013_member;
SET ROLE dcl_03013_grantor;
GRANT USAGE ON FOREIGN SERVER dcl_03013_missing_object TO PUBLIC;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'role_membership' AS privilege_scope;
RESET ROLE;
RESET ALL;
DROP SERVER IF EXISTS dcl_03013_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_03013_fdw CASCADE;
DROP OWNED BY dcl_03013_member;
DROP OWNED BY dcl_03013_grantor;
DROP ROLE IF EXISTS dcl_03013_member;
DROP ROLE IF EXISTS dcl_03013_grantor;
