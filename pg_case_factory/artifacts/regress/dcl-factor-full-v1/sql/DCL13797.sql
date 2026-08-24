-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_5 (domain) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_5
-- factor expected_status=success
-- factor privilege_scope=table_privilege
-- factor grantee_shape=role_name
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=none
-- factor ownership_boundary=owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS dcl_13797_grantee;
DROP ROLE IF EXISTS dcl_13797_grantor;
DROP ROLE IF EXISTS dcl_13797_member;
CREATE ROLE dcl_13797_grantee;
CREATE ROLE dcl_13797_grantor;
CREATE ROLE dcl_13797_member;
DROP DOMAIN IF EXISTS dcl_13797_domain;
CREATE DOMAIN dcl_13797_domain AS text;
GRANT USAGE ON DOMAIN dcl_13797_domain TO dcl_13797_grantee;
SELECT has_type_privilege(CURRENT_USER, 'dcl_13797_domain', 'USAGE');
DROP DOMAIN IF EXISTS dcl_13797_domain;
DROP OWNED BY dcl_13797_grantee;
DROP OWNED BY dcl_13797_member;
DROP OWNED BY dcl_13797_grantor;
DROP ROLE IF EXISTS dcl_13797_member;
DROP ROLE IF EXISTS dcl_13797_grantor;
DROP ROLE IF EXISTS dcl_13797_grantee;
