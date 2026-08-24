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
-- factor grantee_shape=session_user
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
DROP ROLE IF EXISTS "dcl_01855_Grantee";
DROP ROLE IF EXISTS dcl_01855_grantor;
DROP ROLE IF EXISTS dcl_01855_member;
CREATE ROLE "dcl_01855_Grantee";
CREATE ROLE dcl_01855_grantor;
CREATE ROLE dcl_01855_member;
DROP DOMAIN IF EXISTS dcl_01855_domain;
CREATE DOMAIN dcl_01855_domain AS text;
GRANT USAGE ON DOMAIN dcl_01855_domain TO dcl_01855_grantor WITH GRANT OPTION;
SET ROLE dcl_01855_grantor;
GRANT USAGE ON DOMAIN dcl_01855_domain TO SESSION_USER;
RESET ROLE;
SELECT has_type_privilege(CURRENT_USER, 'dcl_01855_domain', 'USAGE');
RESET ROLE;
RESET ALL;
DROP DOMAIN IF EXISTS dcl_01855_domain;
DROP OWNED BY "dcl_01855_Grantee";
DROP OWNED BY dcl_01855_member;
DROP OWNED BY dcl_01855_grantor;
DROP ROLE IF EXISTS dcl_01855_member;
DROP ROLE IF EXISTS dcl_01855_grantor;
DROP ROLE IF EXISTS "dcl_01855_Grantee";
