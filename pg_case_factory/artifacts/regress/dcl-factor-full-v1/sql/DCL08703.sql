-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_5 (domain) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_5
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=session_user
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
DROP ROLE IF EXISTS "dcl_08703_Grantee";
DROP ROLE IF EXISTS dcl_08703_grantor;
DROP ROLE IF EXISTS dcl_08703_member;
CREATE ROLE "dcl_08703_Grantee";
CREATE ROLE dcl_08703_grantor;
CREATE ROLE dcl_08703_member;
DROP DOMAIN IF EXISTS dcl_08703_domain;
CREATE DOMAIN dcl_08703_domain AS text;
GRANT USAGE ON DOMAIN dcl_08703_missing_object TO SESSION_USER;
SET ROLE "dcl_08703_Grantee";
REVOKE ADMIN OPTION FOR USAGE ON DOMAIN dcl_08703_missing_object FROM SESSION_USER GRANTED BY dcl_08703_grantor RESTRICT;
RESET ROLE;
SELECT has_type_privilege(CURRENT_USER, 'dcl_08703_domain', 'USAGE');
DROP DOMAIN IF EXISTS dcl_08703_domain;
DROP OWNED BY "dcl_08703_Grantee";
DROP OWNED BY dcl_08703_member;
DROP OWNED BY dcl_08703_grantor;
DROP ROLE IF EXISTS dcl_08703_member;
DROP ROLE IF EXISTS dcl_08703_grantor;
DROP ROLE IF EXISTS "dcl_08703_Grantee";
