-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_12 (schema) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_12
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
-- factor grantee_shape=public
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
DROP ROLE IF EXISTS dcl_05083_grantor;
DROP ROLE IF EXISTS dcl_05083_member;
CREATE ROLE dcl_05083_grantor;
CREATE ROLE dcl_05083_member;
DROP SCHEMA IF EXISTS dcl_05083_schema CASCADE;
CREATE SCHEMA dcl_05083_schema;
GRANT USAGE ON SCHEMA dcl_05083_missing_object TO dcl_05083_grantor WITH GRANT OPTION;
GRANT dcl_05083_grantor TO dcl_05083_member WITH SET TRUE;
SET ROLE dcl_05083_member;
SET ROLE dcl_05083_grantor;
GRANT USAGE ON SCHEMA dcl_05083_missing_object TO PUBLIC;
RESET ROLE;
SELECT has_schema_privilege(CURRENT_USER, 'dcl_05083_schema', 'USAGE');
RESET ROLE;
RESET ALL;
DROP SCHEMA IF EXISTS dcl_05083_schema CASCADE;
DROP OWNED BY dcl_05083_member;
DROP OWNED BY dcl_05083_grantor;
DROP ROLE IF EXISTS dcl_05083_member;
DROP ROLE IF EXISTS dcl_05083_grantor;
