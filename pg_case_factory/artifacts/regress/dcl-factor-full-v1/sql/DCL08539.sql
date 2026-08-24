-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_4 (database) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_4
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=current_user
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
DROP ROLE IF EXISTS dcl_08539_grantor;
DROP ROLE IF EXISTS dcl_08539_member;
CREATE ROLE dcl_08539_grantor;
CREATE ROLE dcl_08539_member;
GRANT CONNECT ON DATABASE dcl_08539_missing_object TO CURRENT_USER;
GRANT CONNECT ON DATABASE dcl_08539_missing_object TO dcl_08539_grantor WITH GRANT OPTION;
GRANT dcl_08539_grantor TO dcl_08539_member WITH SET TRUE;
SET ROLE dcl_08539_member;
SET ROLE dcl_08539_grantor;
REVOKE ADMIN OPTION FOR CONNECT ON DATABASE dcl_08539_missing_object FROM CURRENT_USER RESTRICT;
RESET ROLE;
SELECT has_database_privilege(CURRENT_USER, 'dcl_08539_database', 'CONNECT');
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_08539_member;
DROP OWNED BY dcl_08539_grantor;
DROP ROLE IF EXISTS dcl_08539_member;
DROP ROLE IF EXISTS dcl_08539_grantor;
