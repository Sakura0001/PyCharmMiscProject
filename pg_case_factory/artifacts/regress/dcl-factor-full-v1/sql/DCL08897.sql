-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_5 (domain) with scope=role_membership
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_5
-- factor expected_status=failure
-- factor privilege_scope=role_membership
-- factor grantee_shape=role_name
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=returned_rows
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_08897_grantee;
DROP ROLE IF EXISTS dcl_08897_grantor;
DROP ROLE IF EXISTS dcl_08897_member;
CREATE ROLE dcl_08897_grantee;
CREATE ROLE dcl_08897_grantor;
CREATE ROLE dcl_08897_member;
DROP DOMAIN IF EXISTS dcl_08897_domain;
CREATE DOMAIN dcl_08897_domain AS text;
GRANT USAGE ON DOMAIN dcl_08897_missing_object TO dcl_08897_grantee;
BEGIN;
SET ROLE dcl_08897_grantee;
REVOKE INHERIT OPTION FOR USAGE ON DOMAIN dcl_08897_missing_object FROM dcl_08897_grantee GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'role_membership' AS privilege_scope;
ROLLBACK;
DROP DOMAIN IF EXISTS dcl_08897_domain;
DROP OWNED BY dcl_08897_grantee;
DROP OWNED BY dcl_08897_member;
DROP OWNED BY dcl_08897_grantor;
DROP ROLE IF EXISTS dcl_08897_member;
DROP ROLE IF EXISTS dcl_08897_grantor;
DROP ROLE IF EXISTS dcl_08897_grantee;
