-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_14 (type) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=public
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
DROP ROLE IF EXISTS "dcl_12831_Grantee";
DROP ROLE IF EXISTS dcl_12831_grantor;
DROP ROLE IF EXISTS dcl_12831_member;
CREATE ROLE "dcl_12831_Grantee";
CREATE ROLE dcl_12831_grantor;
CREATE ROLE dcl_12831_member;
DROP TYPE IF EXISTS dcl_12831_type;
CREATE TYPE dcl_12831_type AS ENUM ('alpha', 'beta');
GRANT USAGE ON TYPE dcl_12831_missing_object TO PUBLIC;
SET ROLE "dcl_12831_Grantee";
REVOKE USAGE ON TYPE dcl_12831_missing_object FROM PUBLIC GRANTED BY dcl_12831_grantor RESTRICT;
RESET ROLE;
SELECT has_type_privilege(CURRENT_USER, 'dcl_12831_type', 'USAGE');
DROP TYPE IF EXISTS dcl_12831_type;
DROP OWNED BY "dcl_12831_Grantee";
DROP OWNED BY dcl_12831_member;
DROP OWNED BY dcl_12831_grantor;
DROP ROLE IF EXISTS dcl_12831_member;
DROP ROLE IF EXISTS dcl_12831_grantor;
DROP ROLE IF EXISTS "dcl_12831_Grantee";
