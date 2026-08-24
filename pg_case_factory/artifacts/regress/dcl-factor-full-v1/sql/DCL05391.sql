-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_12 (schema) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_12
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
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
DROP ROLE IF EXISTS "dcl_05391_Grantee";
DROP ROLE IF EXISTS dcl_05391_grantor;
DROP ROLE IF EXISTS dcl_05391_member;
CREATE ROLE "dcl_05391_Grantee";
CREATE ROLE dcl_05391_grantor;
CREATE ROLE dcl_05391_member;
DROP SCHEMA IF EXISTS dcl_05391_schema CASCADE;
CREATE SCHEMA dcl_05391_schema;
SET ROLE "dcl_05391_Grantee";
GRANT USAGE ON SCHEMA dcl_05391_missing_object TO PUBLIC WITH ADMIN OPTION GRANTED BY dcl_05391_grantor;
RESET ROLE;
SELECT has_schema_privilege(CURRENT_USER, 'dcl_05391_schema', 'USAGE');
DROP SCHEMA IF EXISTS dcl_05391_schema CASCADE;
DROP OWNED BY "dcl_05391_Grantee";
DROP OWNED BY dcl_05391_member;
DROP OWNED BY dcl_05391_grantor;
DROP ROLE IF EXISTS dcl_05391_member;
DROP ROLE IF EXISTS dcl_05391_grantor;
DROP ROLE IF EXISTS "dcl_05391_Grantee";
