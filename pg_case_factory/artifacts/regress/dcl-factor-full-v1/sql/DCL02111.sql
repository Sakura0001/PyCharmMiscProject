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
-- factor grantee_shape=role_name
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_02111_grantee;
DROP ROLE IF EXISTS dcl_02111_grantor;
DROP ROLE IF EXISTS dcl_02111_member;
CREATE ROLE dcl_02111_grantee;
CREATE ROLE dcl_02111_grantor;
CREATE ROLE dcl_02111_member;
DROP DOMAIN IF EXISTS dcl_02111_domain;
CREATE DOMAIN dcl_02111_domain AS text;
BEGIN;
SET ROLE dcl_02111_grantee;
GRANT USAGE ON DOMAIN dcl_02111_missing_object TO dcl_02111_grantee WITH INHERIT TRUE GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT has_type_privilege(CURRENT_USER, 'dcl_02111_domain', 'USAGE');
ROLLBACK;
DROP DOMAIN IF EXISTS dcl_02111_domain;
DROP OWNED BY dcl_02111_grantee;
DROP OWNED BY dcl_02111_member;
DROP OWNED BY dcl_02111_grantor;
DROP ROLE IF EXISTS dcl_02111_member;
DROP ROLE IF EXISTS dcl_02111_grantor;
DROP ROLE IF EXISTS dcl_02111_grantee;
