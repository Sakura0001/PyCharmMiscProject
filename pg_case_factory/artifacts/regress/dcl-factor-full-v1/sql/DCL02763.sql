-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_7 (foreign_server) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_7
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=role_name
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=insufficient_privilege
-- factor invalid_combination=syntax_valid_semantic_error
-- factor ownership_boundary=owner
-- factor verification_mode=catalog_query
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_02763_Grantee";
DROP ROLE IF EXISTS dcl_02763_grantor;
DROP ROLE IF EXISTS dcl_02763_member;
CREATE ROLE "dcl_02763_Grantee";
CREATE ROLE dcl_02763_grantor;
CREATE ROLE dcl_02763_member;
DROP SERVER IF EXISTS dcl_02763_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02763_fdw CASCADE;
CREATE FOREIGN DATA WRAPPER dcl_02763_fdw;
CREATE SERVER dcl_02763_server FOREIGN DATA WRAPPER dcl_02763_fdw;
SET ROLE "dcl_02763_Grantee";
GRANT USAGE ON FOREIGN SERVER dcl_02763_missing_object TO "dcl_02763_Grantee" GRANTED BY dcl_02763_grantor;
RESET ROLE;
SELECT true AS foreign_server_privilege_statement_completed;
DROP SERVER IF EXISTS dcl_02763_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS dcl_02763_fdw CASCADE;
DROP OWNED BY "dcl_02763_Grantee";
DROP OWNED BY dcl_02763_member;
DROP OWNED BY dcl_02763_grantor;
DROP ROLE IF EXISTS dcl_02763_member;
DROP ROLE IF EXISTS dcl_02763_grantor;
DROP ROLE IF EXISTS "dcl_02763_Grantee";
