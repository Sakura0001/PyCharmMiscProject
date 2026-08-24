-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_13 (tablespace) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_13
-- factor expected_status=success
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=role_name
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
DROP ROLE IF EXISTS dcl_05434_grantee;
DROP ROLE IF EXISTS dcl_05434_grantor;
DROP ROLE IF EXISTS dcl_05434_member;
CREATE ROLE dcl_05434_grantee;
CREATE ROLE dcl_05434_grantor;
CREATE ROLE dcl_05434_member;
GRANT CREATE ON TABLESPACE dcl_05434_tablespace TO dcl_05434_grantee WITH GRANT OPTION;
SELECT has_tablespace_privilege(CURRENT_USER, 'dcl_05434_tablespace', 'CREATE');
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_05434_grantee;
DROP OWNED BY dcl_05434_member;
DROP OWNED BY dcl_05434_grantor;
DROP ROLE IF EXISTS dcl_05434_member;
DROP ROLE IF EXISTS dcl_05434_grantor;
DROP ROLE IF EXISTS dcl_05434_grantee;
