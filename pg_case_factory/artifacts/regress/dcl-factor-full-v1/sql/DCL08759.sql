-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_5 (domain) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_5
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
-- factor grantee_shape=session_user
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_08759_grantee;
DROP ROLE IF EXISTS dcl_08759_grantor;
DROP ROLE IF EXISTS dcl_08759_member;
CREATE ROLE dcl_08759_grantee;
CREATE ROLE dcl_08759_grantor;
CREATE ROLE dcl_08759_member;
DROP DOMAIN IF EXISTS dcl_08759_domain;
CREATE DOMAIN dcl_08759_domain AS text;
GRANT USAGE ON DOMAIN dcl_08759_missing_object TO SESSION_USER;
BEGIN;
SET ROLE dcl_08759_grantee;
REVOKE GRANT OPTION FOR USAGE ON DOMAIN dcl_08759_missing_object FROM SESSION_USER GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT has_type_privilege(CURRENT_USER, 'dcl_08759_domain', 'USAGE');
ROLLBACK;
DROP DOMAIN IF EXISTS dcl_08759_domain;
DROP OWNED BY dcl_08759_grantee;
DROP OWNED BY dcl_08759_member;
DROP OWNED BY dcl_08759_grantor;
DROP ROLE IF EXISTS dcl_08759_member;
DROP ROLE IF EXISTS dcl_08759_grantor;
DROP ROLE IF EXISTS dcl_08759_grantee;
