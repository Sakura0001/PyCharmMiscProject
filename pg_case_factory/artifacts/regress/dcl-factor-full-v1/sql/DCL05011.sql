-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_12 (schema) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_12
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=role_name
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
DROP ROLE IF EXISTS dcl_05011_grantor;
DROP ROLE IF EXISTS dcl_05011_member;
CREATE ROLE dcl_05011_grantor;
CREATE ROLE dcl_05011_member;
DROP SCHEMA IF EXISTS dcl_05011_schema CASCADE;
CREATE SCHEMA dcl_05011_schema;
GRANT USAGE ON SCHEMA dcl_05011_missing_object TO dcl_05011_grantor WITH GRANT OPTION;
GRANT dcl_05011_grantor TO dcl_05011_member WITH SET TRUE;
SET ROLE dcl_05011_member;
SET ROLE dcl_05011_grantor;
GRANT USAGE ON SCHEMA dcl_05011_missing_object TO dcl_05011_missing_role;
RESET ROLE;
SELECT has_schema_privilege(CURRENT_USER, 'dcl_05011_schema', 'USAGE');
RESET ROLE;
RESET ALL;
DROP SCHEMA IF EXISTS dcl_05011_schema CASCADE;
DROP OWNED BY dcl_05011_member;
DROP OWNED BY dcl_05011_grantor;
DROP ROLE IF EXISTS dcl_05011_member;
DROP ROLE IF EXISTS dcl_05011_grantor;
