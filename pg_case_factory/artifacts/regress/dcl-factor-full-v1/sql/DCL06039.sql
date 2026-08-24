-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_14 (type) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=role_name
-- factor grant_option_shape=admin_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_06039_Grantee";
DROP ROLE IF EXISTS dcl_06039_grantor;
DROP ROLE IF EXISTS dcl_06039_member;
CREATE ROLE "dcl_06039_Grantee";
CREATE ROLE dcl_06039_grantor;
CREATE ROLE dcl_06039_member;
DROP TYPE IF EXISTS dcl_06039_type;
CREATE TYPE dcl_06039_type AS ENUM ('alpha', 'beta');
SET ROLE "dcl_06039_Grantee";
GRANT USAGE ON TYPE dcl_06039_missing_object TO "dcl_06039_Grantee" WITH ADMIN OPTION GRANTED BY dcl_06039_grantor;
RESET ROLE;
SELECT has_type_privilege(CURRENT_USER, 'dcl_06039_type', 'USAGE');
DROP TYPE IF EXISTS dcl_06039_type;
DROP OWNED BY "dcl_06039_Grantee";
DROP OWNED BY dcl_06039_member;
DROP OWNED BY dcl_06039_grantor;
DROP ROLE IF EXISTS dcl_06039_member;
DROP ROLE IF EXISTS dcl_06039_grantor;
DROP ROLE IF EXISTS "dcl_06039_Grantee";
