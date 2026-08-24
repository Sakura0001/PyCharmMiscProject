-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_2 (column) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
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
DROP TABLE IF EXISTS dcl_07605_table;
DROP ROLE IF EXISTS "dcl_07605_Grantee";
DROP ROLE IF EXISTS dcl_07605_grantor;
DROP ROLE IF EXISTS dcl_07605_member;
CREATE ROLE "dcl_07605_Grantee";
CREATE ROLE dcl_07605_grantor;
CREATE ROLE dcl_07605_member;
CREATE TABLE dcl_07605_table (id integer, payload text);
GRANT EXECUTE (payload) ON TABLE dcl_07605_missing_object TO "dcl_07605_Grantee";
SET ROLE "dcl_07605_Grantee";
REVOKE ADMIN OPTION FOR EXECUTE (payload) ON TABLE dcl_07605_missing_object FROM "dcl_07605_Grantee" GRANTED BY dcl_07605_grantor RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'parameter_privilege' AS privilege_scope;
DROP OWNED BY "dcl_07605_Grantee";
DROP OWNED BY dcl_07605_member;
DROP OWNED BY dcl_07605_grantor;
DROP ROLE IF EXISTS dcl_07605_member;
DROP ROLE IF EXISTS dcl_07605_grantor;
DROP ROLE IF EXISTS "dcl_07605_Grantee";
DROP TABLE IF EXISTS dcl_07605_table;
