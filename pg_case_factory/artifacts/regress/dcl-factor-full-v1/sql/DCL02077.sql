-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_5 (domain) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_5
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=current_user
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
DROP ROLE IF EXISTS dcl_02077_grantor;
DROP ROLE IF EXISTS dcl_02077_member;
CREATE ROLE dcl_02077_grantor;
CREATE ROLE dcl_02077_member;
DROP DOMAIN IF EXISTS dcl_02077_domain;
CREATE DOMAIN dcl_02077_domain AS text;
GRANT USAGE ON DOMAIN dcl_02077_missing_object TO dcl_02077_grantor WITH GRANT OPTION;
GRANT dcl_02077_grantor TO dcl_02077_member WITH SET TRUE;
SET ROLE dcl_02077_member;
SET ROLE dcl_02077_grantor;
GRANT USAGE ON DOMAIN dcl_02077_missing_object TO CURRENT_USER;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'routine_language_type_fdw_server' AS privilege_scope;
RESET ROLE;
RESET ALL;
DROP DOMAIN IF EXISTS dcl_02077_domain;
DROP OWNED BY dcl_02077_member;
DROP OWNED BY dcl_02077_grantor;
DROP ROLE IF EXISTS dcl_02077_member;
DROP ROLE IF EXISTS dcl_02077_grantor;
