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
DROP ROLE IF EXISTS "dcl_08499_Grantee";
DROP ROLE IF EXISTS dcl_08499_grantor;
DROP ROLE IF EXISTS dcl_08499_member;
CREATE ROLE "dcl_08499_Grantee";
CREATE ROLE dcl_08499_grantor;
CREATE ROLE dcl_08499_member;
GRANT CONNECT ON DATABASE dcl_08499_missing_object TO "dcl_08499_Grantee";
SET ROLE "dcl_08499_Grantee";
REVOKE CONNECT ON DATABASE dcl_08499_missing_object FROM "dcl_08499_Grantee" GRANTED BY dcl_08499_grantor RESTRICT;
RESET ROLE;
SELECT has_database_privilege(CURRENT_USER, 'dcl_08499_database', 'CONNECT');
DROP OWNED BY "dcl_08499_Grantee";
DROP OWNED BY dcl_08499_member;
DROP OWNED BY dcl_08499_grantor;
DROP ROLE IF EXISTS dcl_08499_member;
DROP ROLE IF EXISTS dcl_08499_grantor;
DROP ROLE IF EXISTS "dcl_08499_Grantee";
