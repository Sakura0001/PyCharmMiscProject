-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_2 (column) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=success
-- factor privilege_scope=column_privilege
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
DROP TABLE IF EXISTS dcl_00501_table;
DROP ROLE IF EXISTS "dcl_00501_Grantee";
DROP ROLE IF EXISTS dcl_00501_grantor;
DROP ROLE IF EXISTS dcl_00501_member;
CREATE ROLE "dcl_00501_Grantee";
CREATE ROLE dcl_00501_grantor;
CREATE ROLE dcl_00501_member;
CREATE TABLE dcl_00501_table (id integer, payload text);
GRANT SELECT (payload) ON TABLE dcl_00501_table TO dcl_00501_grantor WITH GRANT OPTION;
SET ROLE dcl_00501_grantor;
GRANT SELECT (payload) ON TABLE dcl_00501_table TO CURRENT_USER GRANTED BY dcl_00501_grantor;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'column_privilege' AS privilege_scope;
DROP OWNED BY "dcl_00501_Grantee";
DROP OWNED BY dcl_00501_member;
DROP OWNED BY dcl_00501_grantor;
DROP ROLE IF EXISTS dcl_00501_member;
DROP ROLE IF EXISTS dcl_00501_grantor;
DROP ROLE IF EXISTS "dcl_00501_Grantee";
DROP TABLE IF EXISTS dcl_00501_table;
