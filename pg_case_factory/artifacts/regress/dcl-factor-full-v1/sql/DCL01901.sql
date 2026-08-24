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
-- factor grantee_shape=current_user
-- factor grant_option_shape=grant_option
-- factor grantor_shape=granted_by_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=plain_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=non_owner
-- factor verification_mode=returned_rows
-- factor cleanup_mode=rollback
DROP ROLE IF EXISTS dcl_01901_grantee;
DROP ROLE IF EXISTS dcl_01901_grantor;
DROP ROLE IF EXISTS dcl_01901_member;
CREATE ROLE dcl_01901_grantee;
CREATE ROLE dcl_01901_grantor;
CREATE ROLE dcl_01901_member;
DROP DOMAIN IF EXISTS dcl_01901_domain;
CREATE DOMAIN dcl_01901_domain AS text;
BEGIN;
SET ROLE dcl_01901_grantee;
GRANT USAGE ON DOMAIN dcl_01901_missing_object TO CURRENT_USER WITH GRANT OPTION GRANTED BY CURRENT_USER;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'table_privilege' AS privilege_scope;
ROLLBACK;
DROP DOMAIN IF EXISTS dcl_01901_domain;
DROP OWNED BY dcl_01901_grantee;
DROP OWNED BY dcl_01901_member;
DROP OWNED BY dcl_01901_grantor;
DROP ROLE IF EXISTS dcl_01901_member;
DROP ROLE IF EXISTS dcl_01901_grantor;
DROP ROLE IF EXISTS dcl_01901_grantee;
