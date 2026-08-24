-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_5 (domain) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_5
-- factor expected_status=failure
-- factor privilege_scope=routine_language_type_fdw_server
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
DROP ROLE IF EXISTS "dcl_08847_Grantee";
DROP ROLE IF EXISTS dcl_08847_grantor;
DROP ROLE IF EXISTS dcl_08847_member;
CREATE ROLE "dcl_08847_Grantee";
CREATE ROLE dcl_08847_grantor;
CREATE ROLE dcl_08847_member;
DROP DOMAIN IF EXISTS dcl_08847_domain;
CREATE DOMAIN dcl_08847_domain AS text;
GRANT USAGE ON DOMAIN dcl_08847_missing_object TO PUBLIC;
SET ROLE "dcl_08847_Grantee";
REVOKE ADMIN OPTION FOR USAGE ON DOMAIN dcl_08847_missing_object FROM PUBLIC GRANTED BY dcl_08847_grantor RESTRICT;
RESET ROLE;
SELECT has_type_privilege(CURRENT_USER, 'dcl_08847_domain', 'USAGE');
DROP DOMAIN IF EXISTS dcl_08847_domain;
DROP OWNED BY "dcl_08847_Grantee";
DROP OWNED BY dcl_08847_member;
DROP OWNED BY dcl_08847_grantor;
DROP ROLE IF EXISTS dcl_08847_member;
DROP ROLE IF EXISTS dcl_08847_grantor;
DROP ROLE IF EXISTS "dcl_08847_Grantee";
