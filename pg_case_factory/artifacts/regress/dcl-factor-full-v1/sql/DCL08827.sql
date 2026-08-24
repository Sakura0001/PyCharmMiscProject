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
-- factor grantee_shape=role_name
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
DROP ROLE IF EXISTS dcl_08827_grantor;
DROP ROLE IF EXISTS dcl_08827_member;
CREATE ROLE dcl_08827_grantor;
CREATE ROLE dcl_08827_member;
DROP DOMAIN IF EXISTS dcl_08827_domain;
CREATE DOMAIN dcl_08827_domain AS text;
GRANT USAGE ON DOMAIN dcl_08827_missing_object TO dcl_08827_missing_role;
GRANT USAGE ON DOMAIN dcl_08827_missing_object TO dcl_08827_grantor WITH GRANT OPTION;
GRANT dcl_08827_grantor TO dcl_08827_member WITH SET TRUE;
SET ROLE dcl_08827_member;
SET ROLE dcl_08827_grantor;
REVOKE USAGE ON DOMAIN dcl_08827_missing_object FROM dcl_08827_missing_role RESTRICT;
RESET ROLE;
SELECT has_type_privilege(CURRENT_USER, 'dcl_08827_domain', 'USAGE');
RESET ROLE;
RESET ALL;
DROP DOMAIN IF EXISTS dcl_08827_domain;
DROP OWNED BY dcl_08827_member;
DROP OWNED BY dcl_08827_grantor;
DROP ROLE IF EXISTS dcl_08827_member;
DROP ROLE IF EXISTS dcl_08827_grantor;
