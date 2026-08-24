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
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=public
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
DROP ROLE IF EXISTS dcl_01883_grantee;
DROP ROLE IF EXISTS dcl_01883_grantor;
DROP ROLE IF EXISTS dcl_01883_member;
CREATE ROLE dcl_01883_grantee;
CREATE ROLE dcl_01883_grantor;
CREATE ROLE dcl_01883_member;
DROP DOMAIN IF EXISTS dcl_01883_domain;
CREATE DOMAIN dcl_01883_domain AS text;
BEGIN;
SET ROLE dcl_01883_grantee;
GRANT USAGE ON DOMAIN dcl_01883_missing_object TO PUBLIC WITH INHERIT TRUE GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT has_type_privilege(CURRENT_USER, 'dcl_01883_domain', 'USAGE');
ROLLBACK;
DROP DOMAIN IF EXISTS dcl_01883_domain;
DROP OWNED BY dcl_01883_grantee;
DROP OWNED BY dcl_01883_member;
DROP OWNED BY dcl_01883_grantor;
DROP ROLE IF EXISTS dcl_01883_member;
DROP ROLE IF EXISTS dcl_01883_grantor;
DROP ROLE IF EXISTS dcl_01883_grantee;
