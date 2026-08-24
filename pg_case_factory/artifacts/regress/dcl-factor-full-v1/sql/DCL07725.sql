-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_3 (sequence) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_3
-- factor expected_status=success
-- factor privilege_scope=table_privilege
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
DROP ROLE IF EXISTS "dcl_07725_Grantee";
DROP ROLE IF EXISTS dcl_07725_grantor;
DROP ROLE IF EXISTS dcl_07725_member;
CREATE ROLE "dcl_07725_Grantee";
CREATE ROLE dcl_07725_grantor;
CREATE ROLE dcl_07725_member;
DROP SEQUENCE IF EXISTS dcl_07725_sequence;
CREATE SEQUENCE dcl_07725_sequence;
GRANT USAGE ON SEQUENCE dcl_07725_sequence TO PUBLIC;
GRANT USAGE ON SEQUENCE dcl_07725_sequence TO dcl_07725_grantor WITH GRANT OPTION;
SET ROLE dcl_07725_grantor;
REVOKE USAGE ON SEQUENCE dcl_07725_sequence FROM PUBLIC GRANTED BY dcl_07725_grantor RESTRICT;
RESET ROLE;
SELECT 'revoke' AS completed_statement, 'table_privilege' AS privilege_scope;
DROP SEQUENCE IF EXISTS dcl_07725_sequence;
DROP OWNED BY "dcl_07725_Grantee";
DROP OWNED BY dcl_07725_member;
DROP OWNED BY dcl_07725_grantor;
DROP ROLE IF EXISTS dcl_07725_member;
DROP ROLE IF EXISTS dcl_07725_grantor;
DROP ROLE IF EXISTS "dcl_07725_Grantee";
