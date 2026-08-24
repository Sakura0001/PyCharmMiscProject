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
-- factor grantee_shape=current_role
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=missing_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_08671_grantor;
DROP ROLE IF EXISTS dcl_08671_member;
CREATE ROLE dcl_08671_grantor;
CREATE ROLE dcl_08671_member;
DROP DOMAIN IF EXISTS dcl_08671_domain;
CREATE DOMAIN dcl_08671_domain AS text;
GRANT USAGE ON DOMAIN dcl_08671_missing_object TO CURRENT_ROLE;
GRANT USAGE ON DOMAIN dcl_08671_missing_object TO dcl_08671_grantor WITH GRANT OPTION;
GRANT dcl_08671_grantor TO dcl_08671_member WITH SET TRUE;
SET ROLE dcl_08671_member;
SET ROLE dcl_08671_grantor;
REVOKE USAGE ON DOMAIN dcl_08671_missing_object FROM CURRENT_ROLE RESTRICT;
RESET ROLE;
SELECT has_type_privilege(CURRENT_USER, 'dcl_08671_domain', 'USAGE');
RESET ROLE;
RESET ALL;
DROP DOMAIN IF EXISTS dcl_08671_domain;
DROP OWNED BY dcl_08671_member;
DROP OWNED BY dcl_08671_grantor;
DROP ROLE IF EXISTS dcl_08671_member;
DROP ROLE IF EXISTS dcl_08671_grantor;
