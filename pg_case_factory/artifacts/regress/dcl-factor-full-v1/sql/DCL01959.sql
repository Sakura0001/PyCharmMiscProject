-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_5 (domain) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_5
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
-- factor grantee_shape=current_user
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
DROP ROLE IF EXISTS "dcl_01959_Grantee";
DROP ROLE IF EXISTS dcl_01959_grantor;
DROP ROLE IF EXISTS dcl_01959_member;
CREATE ROLE "dcl_01959_Grantee";
CREATE ROLE dcl_01959_grantor;
CREATE ROLE dcl_01959_member;
DROP DOMAIN IF EXISTS dcl_01959_domain;
CREATE DOMAIN dcl_01959_domain AS text;
SET ROLE "dcl_01959_Grantee";
GRANT USAGE ON DOMAIN dcl_01959_missing_object TO CURRENT_USER GRANTED BY dcl_01959_grantor;
RESET ROLE;
SELECT has_type_privilege(CURRENT_USER, 'dcl_01959_domain', 'USAGE');
DROP DOMAIN IF EXISTS dcl_01959_domain;
DROP OWNED BY "dcl_01959_Grantee";
DROP OWNED BY dcl_01959_member;
DROP OWNED BY dcl_01959_grantor;
DROP ROLE IF EXISTS dcl_01959_member;
DROP ROLE IF EXISTS dcl_01959_grantor;
DROP ROLE IF EXISTS "dcl_01959_Grantee";
