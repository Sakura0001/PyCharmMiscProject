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
-- factor grantee_shape=session_user
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=returned_rows
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_09057_Grantee";
DROP ROLE IF EXISTS dcl_09057_grantor;
DROP ROLE IF EXISTS dcl_09057_member;
CREATE ROLE "dcl_09057_Grantee";
CREATE ROLE dcl_09057_grantor;
CREATE ROLE dcl_09057_member;
DROP DOMAIN IF EXISTS dcl_09057_domain;
CREATE DOMAIN dcl_09057_domain AS text;
GRANT USAGE ON DOMAIN dcl_09057_missing_object TO SESSION_USER;
SET ROLE "dcl_09057_Grantee";
REVOKE USAGE ON DOMAIN dcl_09057_missing_object FROM SESSION_USER GRANTED BY dcl_09057_grantor RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'table_maintain' AS privilege_scope;
DROP DOMAIN IF EXISTS dcl_09057_domain;
DROP OWNED BY "dcl_09057_Grantee";
DROP OWNED BY dcl_09057_member;
DROP OWNED BY dcl_09057_grantor;
DROP ROLE IF EXISTS dcl_09057_member;
DROP ROLE IF EXISTS dcl_09057_grantor;
DROP ROLE IF EXISTS "dcl_09057_Grantee";
