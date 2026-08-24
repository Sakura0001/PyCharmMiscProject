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
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=current_role
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
DROP ROLE IF EXISTS dcl_02515_grantor;
DROP ROLE IF EXISTS dcl_02515_member;
CREATE ROLE dcl_02515_grantor;
CREATE ROLE dcl_02515_member;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02515_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_02515_fdw;
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_02515_missing_object TO dcl_02515_grantor WITH GRANT OPTION;
GRANT dcl_02515_grantor TO dcl_02515_member WITH SET TRUE;
SET ROLE dcl_02515_member;
SET ROLE dcl_02515_grantor;
GRANT USAGE ON FOREIGN DATA WRAPPER dcl_02515_missing_object TO CURRENT_ROLE;
RESET ROLE;
SELECT true AS fdw_privilege_statement_completed;
RESET ROLE;
RESET ALL;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02515_fdw CASCADE;
DROP OWNED BY dcl_02515_member;
DROP OWNED BY dcl_02515_grantor;
DROP ROLE IF EXISTS dcl_02515_member;
DROP ROLE IF EXISTS dcl_02515_grantor;
