-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_14 (type) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
-- factor expected_status=success
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=role_name
-- factor grant_option_shape=absent
-- factor grantor_shape=granted_by_non_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=member_role
-- factor verification_mode=returned_rows
-- factor cleanup_mode=drop_objects
DROP ROLE IF EXISTS "dcl_05883_Grantee";
DROP ROLE IF EXISTS dcl_05883_grantor;
DROP ROLE IF EXISTS dcl_05883_member;
CREATE ROLE "dcl_05883_Grantee";
CREATE ROLE dcl_05883_grantor;
CREATE ROLE dcl_05883_member;
DROP TYPE IF EXISTS dcl_05883_type;
CREATE TYPE dcl_05883_type AS ENUM ('alpha', 'beta');
GRANT USAGE ON TYPE dcl_05883_type TO dcl_05883_grantor WITH GRANT OPTION;
SET ROLE dcl_05883_grantor;
GRANT USAGE ON TYPE dcl_05883_type TO "dcl_05883_Grantee" GRANTED BY dcl_05883_grantor;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'routine_language_type_fdw_server' AS privilege_scope;
DROP TYPE IF EXISTS dcl_05883_type;
DROP OWNED BY "dcl_05883_Grantee";
DROP OWNED BY dcl_05883_member;
DROP OWNED BY dcl_05883_grantor;
DROP ROLE IF EXISTS dcl_05883_member;
DROP ROLE IF EXISTS dcl_05883_grantor;
DROP ROLE IF EXISTS "dcl_05883_Grantee";
