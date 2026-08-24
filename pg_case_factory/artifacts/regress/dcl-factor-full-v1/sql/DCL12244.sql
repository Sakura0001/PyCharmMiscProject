-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_13 (tablespace) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_13
-- factor expected_status=success
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=session_user
-- factor grant_option_shape=grant_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=none
-- factor ownership_boundary=owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_12244_grantee;
DROP ROLE IF EXISTS dcl_12244_grantor;
DROP ROLE IF EXISTS dcl_12244_member;
CREATE ROLE dcl_12244_grantee;
CREATE ROLE dcl_12244_grantor;
CREATE ROLE dcl_12244_member;
GRANT CREATE ON TABLESPACE dcl_12244_tablespace TO SESSION_USER;
REVOKE GRANT OPTION FOR CREATE ON TABLESPACE dcl_12244_tablespace FROM SESSION_USER RESTRICT;
SELECT has_tablespace_privilege(CURRENT_USER, 'dcl_12244_tablespace', 'CREATE');
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_12244_grantee;
DROP OWNED BY dcl_12244_member;
DROP OWNED BY dcl_12244_grantor;
DROP ROLE IF EXISTS dcl_12244_member;
DROP ROLE IF EXISTS dcl_12244_grantor;
DROP ROLE IF EXISTS dcl_12244_grantee;
