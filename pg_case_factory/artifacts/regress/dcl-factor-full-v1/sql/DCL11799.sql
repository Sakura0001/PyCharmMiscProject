-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_12 (schema) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_12
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=role_name
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_11799_Grantee";
DROP ROLE IF EXISTS dcl_11799_grantor;
DROP ROLE IF EXISTS dcl_11799_member;
CREATE ROLE "dcl_11799_Grantee";
CREATE ROLE dcl_11799_grantor;
CREATE ROLE dcl_11799_member;
DROP SCHEMA IF EXISTS dcl_11799_schema CASCADE;
CREATE SCHEMA dcl_11799_schema;
GRANT USAGE ON SCHEMA dcl_11799_missing_object TO "dcl_11799_Grantee";
SET ROLE "dcl_11799_Grantee";
REVOKE USAGE ON SCHEMA dcl_11799_missing_object FROM "dcl_11799_Grantee" GRANTED BY dcl_11799_grantor RESTRICT;
RESET ROLE;
SELECT has_schema_privilege(CURRENT_USER, 'dcl_11799_schema', 'USAGE');
DROP SCHEMA IF EXISTS dcl_11799_schema CASCADE;
DROP OWNED BY "dcl_11799_Grantee";
DROP OWNED BY dcl_11799_member;
DROP OWNED BY dcl_11799_grantor;
DROP ROLE IF EXISTS dcl_11799_member;
DROP ROLE IF EXISTS dcl_11799_grantor;
DROP ROLE IF EXISTS "dcl_11799_Grantee";
