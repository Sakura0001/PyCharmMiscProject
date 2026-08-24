-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_14 (type) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=public
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
DROP ROLE IF EXISTS "dcl_05931_Grantee";
DROP ROLE IF EXISTS dcl_05931_grantor;
DROP ROLE IF EXISTS dcl_05931_member;
CREATE ROLE "dcl_05931_Grantee";
CREATE ROLE dcl_05931_grantor;
CREATE ROLE dcl_05931_member;
DROP TYPE IF EXISTS dcl_05931_type;
CREATE TYPE dcl_05931_type AS ENUM ('alpha', 'beta');
SET ROLE "dcl_05931_Grantee";
GRANT USAGE ON TYPE dcl_05931_missing_object TO PUBLIC WITH ADMIN OPTION GRANTED BY dcl_05931_grantor;
RESET ROLE;
SELECT has_type_privilege(CURRENT_USER, 'dcl_05931_type', 'USAGE');
DROP TYPE IF EXISTS dcl_05931_type;
DROP OWNED BY "dcl_05931_Grantee";
DROP OWNED BY dcl_05931_member;
DROP OWNED BY dcl_05931_grantor;
DROP ROLE IF EXISTS dcl_05931_member;
DROP ROLE IF EXISTS dcl_05931_grantor;
DROP ROLE IF EXISTS "dcl_05931_Grantee";
