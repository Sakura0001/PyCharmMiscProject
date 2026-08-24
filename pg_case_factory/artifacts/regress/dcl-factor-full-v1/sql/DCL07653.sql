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
-- factor grantee_shape=session_user
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
DROP TABLE IF EXISTS dcl_07653_table;
DROP ROLE IF EXISTS "dcl_07653_Grantee";
DROP ROLE IF EXISTS dcl_07653_grantor;
DROP ROLE IF EXISTS dcl_07653_member;
CREATE ROLE "dcl_07653_Grantee";
CREATE ROLE dcl_07653_grantor;
CREATE ROLE dcl_07653_member;
CREATE TABLE dcl_07653_table (id integer, payload text);
GRANT EXECUTE (payload) ON TABLE dcl_07653_missing_object TO SESSION_USER;
SET ROLE "dcl_07653_Grantee";
REVOKE ADMIN OPTION FOR EXECUTE (payload) ON TABLE dcl_07653_missing_object FROM SESSION_USER GRANTED BY dcl_07653_grantor RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'parameter_privilege' AS privilege_scope;
DROP OWNED BY "dcl_07653_Grantee";
DROP OWNED BY dcl_07653_member;
DROP OWNED BY dcl_07653_grantor;
DROP ROLE IF EXISTS dcl_07653_member;
DROP ROLE IF EXISTS dcl_07653_grantor;
DROP ROLE IF EXISTS "dcl_07653_Grantee";
DROP TABLE IF EXISTS dcl_07653_table;
