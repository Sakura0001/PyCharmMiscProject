-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_5 (domain) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_5
-- factor expected_status=success
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=current_role
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=member_role
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS "dcl_01843_Grantee";
DROP ROLE IF EXISTS dcl_01843_grantor;
DROP ROLE IF EXISTS dcl_01843_member;
CREATE ROLE "dcl_01843_Grantee";
CREATE ROLE dcl_01843_grantor;
CREATE ROLE dcl_01843_member;
DROP DOMAIN IF EXISTS dcl_01843_domain;
CREATE DOMAIN dcl_01843_domain AS text;
GRANT USAGE ON DOMAIN dcl_01843_domain TO dcl_01843_grantor WITH GRANT OPTION;
SET ROLE dcl_01843_grantor;
GRANT USAGE ON DOMAIN dcl_01843_domain TO CURRENT_ROLE;
RESET ROLE;
SELECT has_type_privilege(CURRENT_USER, 'dcl_01843_domain', 'USAGE');
RESET ROLE;
RESET ALL;
DROP DOMAIN IF EXISTS dcl_01843_domain;
DROP OWNED BY "dcl_01843_Grantee";
DROP OWNED BY dcl_01843_member;
DROP OWNED BY dcl_01843_grantor;
DROP ROLE IF EXISTS dcl_01843_member;
DROP ROLE IF EXISTS dcl_01843_grantor;
DROP ROLE IF EXISTS "dcl_01843_Grantee";
