-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_14 (type) with scope=routine_language_type_fdw_server
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
-- factor expected_status=success
-- factor privilege_scope=routine_language_type_fdw_server
-- factor grantee_shape=public
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
DROP ROLE IF EXISTS "dcl_12675_Grantee";
DROP ROLE IF EXISTS dcl_12675_grantor;
DROP ROLE IF EXISTS dcl_12675_member;
CREATE ROLE "dcl_12675_Grantee";
CREATE ROLE dcl_12675_grantor;
CREATE ROLE dcl_12675_member;
DROP TYPE IF EXISTS dcl_12675_type;
CREATE TYPE dcl_12675_type AS ENUM ('alpha', 'beta');
GRANT USAGE ON TYPE dcl_12675_type TO PUBLIC;
GRANT USAGE ON TYPE dcl_12675_type TO dcl_12675_grantor WITH GRANT OPTION;
SET ROLE dcl_12675_grantor;
REVOKE USAGE ON TYPE dcl_12675_type FROM PUBLIC GRANTED BY dcl_12675_grantor RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'routine_language_type_fdw_server' AS privilege_scope;
DROP TYPE IF EXISTS dcl_12675_type;
DROP OWNED BY "dcl_12675_Grantee";
DROP OWNED BY dcl_12675_member;
DROP OWNED BY dcl_12675_grantor;
DROP ROLE IF EXISTS dcl_12675_member;
DROP ROLE IF EXISTS dcl_12675_grantor;
DROP ROLE IF EXISTS "dcl_12675_Grantee";
