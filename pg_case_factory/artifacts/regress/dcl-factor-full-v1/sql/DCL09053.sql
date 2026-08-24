-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_5 (domain) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_5
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
-- factor grantee_shape=current_user
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
DROP ROLE IF EXISTS dcl_09053_grantee;
DROP ROLE IF EXISTS dcl_09053_grantor;
DROP ROLE IF EXISTS dcl_09053_member;
CREATE ROLE dcl_09053_grantee;
CREATE ROLE dcl_09053_grantor;
CREATE ROLE dcl_09053_member;
DROP DOMAIN IF EXISTS dcl_09053_domain;
CREATE DOMAIN dcl_09053_domain AS text;
GRANT USAGE ON DOMAIN dcl_09053_missing_object TO CURRENT_USER;
BEGIN;
SET ROLE dcl_09053_grantee;
REVOKE INHERIT OPTION FOR USAGE ON DOMAIN dcl_09053_missing_object FROM CURRENT_USER GRANTED BY CURRENT_USER RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'table_maintain' AS privilege_scope;
ROLLBACK;
DROP DOMAIN IF EXISTS dcl_09053_domain;
DROP OWNED BY dcl_09053_grantee;
DROP OWNED BY dcl_09053_member;
DROP OWNED BY dcl_09053_grantor;
DROP ROLE IF EXISTS dcl_09053_member;
DROP ROLE IF EXISTS dcl_09053_grantor;
DROP ROLE IF EXISTS dcl_09053_grantee;
