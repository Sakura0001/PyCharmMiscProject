-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_5 (domain) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_5
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=role_name
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
DROP ROLE IF EXISTS "dcl_08769_Grantee";
DROP ROLE IF EXISTS dcl_08769_grantor;
DROP ROLE IF EXISTS dcl_08769_member;
CREATE ROLE "dcl_08769_Grantee";
CREATE ROLE dcl_08769_grantor;
CREATE ROLE dcl_08769_member;
DROP DOMAIN IF EXISTS dcl_08769_domain;
CREATE DOMAIN dcl_08769_domain AS text;
GRANT USAGE ON DOMAIN dcl_08769_missing_object TO "dcl_08769_Grantee";
SET ROLE "dcl_08769_Grantee";
REVOKE USAGE ON DOMAIN dcl_08769_missing_object FROM "dcl_08769_Grantee" GRANTED BY dcl_08769_grantor RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'schema_database_tablespace' AS privilege_scope;
DROP DOMAIN IF EXISTS dcl_08769_domain;
DROP OWNED BY "dcl_08769_Grantee";
DROP OWNED BY dcl_08769_member;
DROP OWNED BY dcl_08769_grantor;
DROP ROLE IF EXISTS dcl_08769_member;
DROP ROLE IF EXISTS dcl_08769_grantor;
DROP ROLE IF EXISTS "dcl_08769_Grantee";
