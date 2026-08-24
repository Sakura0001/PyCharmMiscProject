-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_1 (table) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=success
-- factor privilege_scope=table_maintain
-- factor grantee_shape=current_user
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
DROP TABLE IF EXISTS dcl_06837_table;
DROP ROLE IF EXISTS "dcl_06837_Grantee";
DROP ROLE IF EXISTS dcl_06837_grantor;
DROP ROLE IF EXISTS dcl_06837_member;
CREATE ROLE "dcl_06837_Grantee";
CREATE ROLE dcl_06837_grantor;
CREATE ROLE dcl_06837_member;
CREATE TABLE dcl_06837_table (id integer, payload text);
GRANT MAINTAIN ON TABLE dcl_06837_table TO CURRENT_USER;
GRANT MAINTAIN ON TABLE dcl_06837_table TO dcl_06837_grantor WITH GRANT OPTION;
SET ROLE dcl_06837_grantor;
REVOKE MAINTAIN ON TABLE dcl_06837_table FROM CURRENT_USER GRANTED BY dcl_06837_grantor RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'table_maintain' AS privilege_scope;
DROP OWNED BY "dcl_06837_Grantee";
DROP OWNED BY dcl_06837_member;
DROP OWNED BY dcl_06837_grantor;
DROP ROLE IF EXISTS dcl_06837_member;
DROP ROLE IF EXISTS dcl_06837_grantor;
DROP ROLE IF EXISTS "dcl_06837_Grantee";
DROP TABLE IF EXISTS dcl_06837_table;
