-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_2 (column) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=success
-- factor privilege_scope=column_privilege
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
DROP TABLE IF EXISTS dcl_07269_table;
DROP ROLE IF EXISTS "dcl_07269_Grantee";
DROP ROLE IF EXISTS dcl_07269_grantor;
DROP ROLE IF EXISTS dcl_07269_member;
CREATE ROLE "dcl_07269_Grantee";
CREATE ROLE dcl_07269_grantor;
CREATE ROLE dcl_07269_member;
CREATE TABLE dcl_07269_table (id integer, payload text);
GRANT SELECT (payload) ON TABLE dcl_07269_table TO "dcl_07269_Grantee";
GRANT SELECT (payload) ON TABLE dcl_07269_table TO dcl_07269_grantor WITH GRANT OPTION;
SET ROLE dcl_07269_grantor;
REVOKE SELECT (payload) ON TABLE dcl_07269_table FROM "dcl_07269_Grantee" GRANTED BY dcl_07269_grantor RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'column_privilege' AS privilege_scope;
DROP OWNED BY "dcl_07269_Grantee";
DROP OWNED BY dcl_07269_member;
DROP OWNED BY dcl_07269_grantor;
DROP ROLE IF EXISTS dcl_07269_member;
DROP ROLE IF EXISTS dcl_07269_grantor;
DROP ROLE IF EXISTS "dcl_07269_Grantee";
DROP TABLE IF EXISTS dcl_07269_table;
