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
DROP ROLE IF EXISTS dcl_08717_grantee;
DROP ROLE IF EXISTS dcl_08717_grantor;
DROP ROLE IF EXISTS dcl_08717_member;
CREATE ROLE dcl_08717_grantee;
CREATE ROLE dcl_08717_grantor;
CREATE ROLE dcl_08717_member;
DROP DOMAIN IF EXISTS dcl_08717_domain;
CREATE DOMAIN dcl_08717_domain AS text;
GRANT USAGE ON DOMAIN dcl_08717_missing_object TO dcl_08717_grantee;
BEGIN;
SET ROLE dcl_08717_grantee;
REVOKE INHERIT OPTION FOR USAGE ON DOMAIN dcl_08717_missing_object FROM dcl_08717_grantee GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'column_privilege' AS privilege_scope;
ROLLBACK;
DROP DOMAIN IF EXISTS dcl_08717_domain;
DROP OWNED BY dcl_08717_grantee;
DROP OWNED BY dcl_08717_member;
DROP OWNED BY dcl_08717_grantor;
DROP ROLE IF EXISTS dcl_08717_member;
DROP ROLE IF EXISTS dcl_08717_grantor;
DROP ROLE IF EXISTS dcl_08717_grantee;
