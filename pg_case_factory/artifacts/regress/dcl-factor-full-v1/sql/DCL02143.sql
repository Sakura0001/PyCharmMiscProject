-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_5 (domain) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_5
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=current_user
-- factor grant_option_shape=admin_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=missing_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_02143_grantor;
DROP ROLE IF EXISTS dcl_02143_member;
CREATE ROLE dcl_02143_grantor;
CREATE ROLE dcl_02143_member;
DROP DOMAIN IF EXISTS dcl_02143_domain;
CREATE DOMAIN dcl_02143_domain AS text;
GRANT USAGE ON DOMAIN dcl_02143_missing_object TO dcl_02143_grantor WITH GRANT OPTION;
GRANT dcl_02143_grantor TO dcl_02143_member WITH SET TRUE;
SET ROLE dcl_02143_member;
SET ROLE dcl_02143_grantor;
GRANT USAGE ON DOMAIN dcl_02143_missing_object TO CURRENT_USER WITH ADMIN OPTION;
RESET ROLE;
SELECT has_type_privilege(CURRENT_USER, 'dcl_02143_domain', 'USAGE');
RESET ROLE;
RESET ALL;
DROP DOMAIN IF EXISTS dcl_02143_domain;
DROP OWNED BY dcl_02143_member;
DROP OWNED BY dcl_02143_grantor;
DROP ROLE IF EXISTS dcl_02143_member;
DROP ROLE IF EXISTS dcl_02143_grantor;
