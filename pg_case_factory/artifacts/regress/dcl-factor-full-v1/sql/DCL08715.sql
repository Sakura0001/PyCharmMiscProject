-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_5 (domain) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_5
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
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
DROP ROLE IF EXISTS "dcl_08715_Grantee";
DROP ROLE IF EXISTS dcl_08715_grantor;
DROP ROLE IF EXISTS dcl_08715_member;
CREATE ROLE "dcl_08715_Grantee";
CREATE ROLE dcl_08715_grantor;
CREATE ROLE dcl_08715_member;
DROP DOMAIN IF EXISTS dcl_08715_domain;
CREATE DOMAIN dcl_08715_domain AS text;
GRANT USAGE ON DOMAIN dcl_08715_missing_object TO "dcl_08715_Grantee";
SET ROLE "dcl_08715_Grantee";
REVOKE ADMIN OPTION FOR USAGE ON DOMAIN dcl_08715_missing_object FROM "dcl_08715_Grantee" GRANTED BY dcl_08715_grantor RESTRICT;
RESET ROLE;
SELECT has_type_privilege(CURRENT_USER, 'dcl_08715_domain', 'USAGE');
DROP DOMAIN IF EXISTS dcl_08715_domain;
DROP OWNED BY "dcl_08715_Grantee";
DROP OWNED BY dcl_08715_member;
DROP OWNED BY dcl_08715_grantor;
DROP ROLE IF EXISTS dcl_08715_member;
DROP ROLE IF EXISTS dcl_08715_grantor;
DROP ROLE IF EXISTS "dcl_08715_Grantee";
