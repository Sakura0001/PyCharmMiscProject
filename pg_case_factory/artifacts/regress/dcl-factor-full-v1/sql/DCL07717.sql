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
-- factor grantee_shape=role_name
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=member_role
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS "dcl_07717_Grantee";
DROP ROLE IF EXISTS dcl_07717_grantor;
DROP ROLE IF EXISTS dcl_07717_member;
CREATE ROLE "dcl_07717_Grantee";
CREATE ROLE dcl_07717_grantor;
CREATE ROLE dcl_07717_member;
DROP SEQUENCE IF EXISTS dcl_07717_sequence;
CREATE SEQUENCE dcl_07717_sequence;
GRANT USAGE ON SEQUENCE dcl_07717_sequence TO "dcl_07717_Grantee";
GRANT USAGE ON SEQUENCE dcl_07717_sequence TO dcl_07717_grantor WITH GRANT OPTION;
SET ROLE dcl_07717_grantor;
REVOKE USAGE ON SEQUENCE dcl_07717_sequence FROM "dcl_07717_Grantee" RESTRICT;
RESET ROLE;
SELECT has_sequence_privilege(CURRENT_USER, 'dcl_07717_sequence', 'USAGE');
RESET ROLE;
RESET ALL;
DROP SEQUENCE IF EXISTS dcl_07717_sequence;
DROP OWNED BY "dcl_07717_Grantee";
DROP OWNED BY dcl_07717_member;
DROP OWNED BY dcl_07717_grantor;
DROP ROLE IF EXISTS dcl_07717_member;
DROP ROLE IF EXISTS dcl_07717_grantor;
DROP ROLE IF EXISTS "dcl_07717_Grantee";
