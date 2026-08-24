-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_5 (domain) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_5
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=role_name
-- factor grant_option_shape=admin_option
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=returned_rows
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_01989_Grantee";
DROP ROLE IF EXISTS dcl_01989_grantor;
DROP ROLE IF EXISTS dcl_01989_member;
CREATE ROLE "dcl_01989_Grantee";
CREATE ROLE dcl_01989_grantor;
CREATE ROLE dcl_01989_member;
DROP DOMAIN IF EXISTS dcl_01989_domain;
CREATE DOMAIN dcl_01989_domain AS text;
SET ROLE "dcl_01989_Grantee";
GRANT USAGE ON DOMAIN dcl_01989_missing_object TO "dcl_01989_Grantee" WITH ADMIN OPTION GRANTED BY dcl_01989_grantor;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'schema_database_tablespace' AS privilege_scope;
DROP DOMAIN IF EXISTS dcl_01989_domain;
DROP OWNED BY "dcl_01989_Grantee";
DROP OWNED BY dcl_01989_member;
DROP OWNED BY dcl_01989_grantor;
DROP ROLE IF EXISTS dcl_01989_member;
DROP ROLE IF EXISTS dcl_01989_grantor;
DROP ROLE IF EXISTS "dcl_01989_Grantee";
