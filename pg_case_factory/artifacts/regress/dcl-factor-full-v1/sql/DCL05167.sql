-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_12 (schema) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_12
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=current_user
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
DROP ROLE IF EXISTS dcl_05167_grantor;
DROP ROLE IF EXISTS dcl_05167_member;
CREATE ROLE dcl_05167_grantor;
CREATE ROLE dcl_05167_member;
DROP SCHEMA IF EXISTS dcl_05167_schema CASCADE;
CREATE SCHEMA dcl_05167_schema;
GRANT USAGE ON SCHEMA dcl_05167_missing_object TO dcl_05167_grantor WITH GRANT OPTION;
GRANT dcl_05167_grantor TO dcl_05167_member WITH SET TRUE;
SET ROLE dcl_05167_member;
SET ROLE dcl_05167_grantor;
GRANT USAGE ON SCHEMA dcl_05167_missing_object TO CURRENT_USER;
RESET ROLE;
SELECT has_schema_privilege(CURRENT_USER, 'dcl_05167_schema', 'USAGE');
RESET ROLE;
RESET ALL;
DROP SCHEMA IF EXISTS dcl_05167_schema CASCADE;
DROP OWNED BY dcl_05167_member;
DROP OWNED BY dcl_05167_grantor;
DROP ROLE IF EXISTS dcl_05167_member;
DROP ROLE IF EXISTS dcl_05167_grantor;
