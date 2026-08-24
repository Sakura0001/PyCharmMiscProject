-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_6 (foreign_data_wrapper) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_6
-- factor expected_status=success
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=role_name
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
DROP ROLE IF EXISTS "dcl_02281_Grantee";
DROP ROLE IF EXISTS dcl_02281_grantor;
DROP ROLE IF EXISTS dcl_02281_member;
CREATE ROLE "dcl_02281_Grantee";
CREATE ROLE dcl_02281_grantor;
CREATE ROLE dcl_02281_member;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02281_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_02281_fdw;
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_02281_fdw TO dcl_02281_grantor WITH GRANT OPTION;
SET ROLE dcl_02281_grantor;
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_02281_fdw TO "dcl_02281_Grantee";
RESET ROLE;
SELECT true AS fdw_privilege_statement_completed;
RESET ROLE;
RESET ALL;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02281_fdw CASCADE;
DROP OWNED BY "dcl_02281_Grantee";
DROP OWNED BY dcl_02281_member;
DROP OWNED BY dcl_02281_grantor;
DROP ROLE IF EXISTS dcl_02281_member;
DROP ROLE IF EXISTS dcl_02281_grantor;
DROP ROLE IF EXISTS "dcl_02281_Grantee";
