-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_11 (parameter) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_11
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=current_role
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
DROP ROLE IF EXISTS dcl_04711_grantor;
DROP ROLE IF EXISTS dcl_04711_member;
CREATE ROLE dcl_04711_grantor;
CREATE ROLE dcl_04711_member;
GRANT SELECT ON PARAMETER work_mem TO dcl_04711_grantor WITH GRANT OPTION;
GRANT dcl_04711_grantor TO dcl_04711_member WITH SET TRUE;
SET ROLE dcl_04711_member;
SET ROLE dcl_04711_grantor;
GRANT SELECT ON PARAMETER work_mem TO CURRENT_ROLE WITH ADMIN OPTION;
RESET ROLE;
SELECT has_parameter_privilege(CURRENT_USER, 'work_mem', 'SET');
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_04711_member;
DROP OWNED BY dcl_04711_grantor;
DROP ROLE IF EXISTS dcl_04711_member;
DROP ROLE IF EXISTS dcl_04711_grantor;
