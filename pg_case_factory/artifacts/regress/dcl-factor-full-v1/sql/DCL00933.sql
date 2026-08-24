-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_3 (sequence) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_3
-- factor expected_status=success
-- factor privilege_scope=table_privilege
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
DROP ROLE IF EXISTS "dcl_00933_Grantee";
DROP ROLE IF EXISTS dcl_00933_grantor;
DROP ROLE IF EXISTS dcl_00933_member;
CREATE ROLE "dcl_00933_Grantee";
CREATE ROLE dcl_00933_grantor;
CREATE ROLE dcl_00933_member;
DROP SEQUENCE IF EXISTS dcl_00933_sequence;
CREATE SEQUENCE dcl_00933_sequence;
GRANT USAGE ON SEQUENCE dcl_00933_sequence TO dcl_00933_grantor WITH GRANT OPTION;
SET ROLE dcl_00933_grantor;
GRANT USAGE ON SEQUENCE dcl_00933_sequence TO "dcl_00933_Grantee" GRANTED BY dcl_00933_grantor;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'table_privilege' AS privilege_scope;
DROP SEQUENCE IF EXISTS dcl_00933_sequence;
DROP OWNED BY "dcl_00933_Grantee";
DROP OWNED BY dcl_00933_member;
DROP OWNED BY dcl_00933_grantor;
DROP ROLE IF EXISTS dcl_00933_member;
DROP ROLE IF EXISTS dcl_00933_grantor;
DROP ROLE IF EXISTS "dcl_00933_Grantee";
