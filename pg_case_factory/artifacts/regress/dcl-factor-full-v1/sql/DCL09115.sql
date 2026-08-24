-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_6 (foreign_data_wrapper) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_6
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=public
-- factor grant_option_shape=admin_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=missing_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_09115_grantor;
DROP ROLE IF EXISTS dcl_09115_member;
CREATE ROLE dcl_09115_grantor;
CREATE ROLE dcl_09115_member;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09115_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_09115_fdw;
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_09115_missing_object TO PUBLIC;
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_09115_missing_object TO dcl_09115_grantor WITH GRANT OPTION;
GRANT dcl_09115_grantor TO dcl_09115_member WITH SET TRUE;
SET ROLE dcl_09115_member;
SET ROLE dcl_09115_grantor;
REVOKE ADMIN OPTION FOR USAGE ON FOREIGN DATA WRAPPER dcl_09115_missing_object FROM PUBLIC RESTRICT;
RESET ROLE;
SELECT true AS fdw_privilege_statement_completed;
RESET ROLE;
RESET ALL;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_09115_fdw CASCADE;
DROP OWNED BY dcl_09115_member;
DROP OWNED BY dcl_09115_grantor;
DROP ROLE IF EXISTS dcl_09115_member;
DROP ROLE IF EXISTS dcl_09115_grantor;
