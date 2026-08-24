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
-- factor grantee_shape=current_user
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
DROP ROLE IF EXISTS "dcl_07735_Grantee";
DROP ROLE IF EXISTS dcl_07735_grantor;
DROP ROLE IF EXISTS dcl_07735_member;
CREATE ROLE "dcl_07735_Grantee";
CREATE ROLE dcl_07735_grantor;
CREATE ROLE dcl_07735_member;
DROP SEQUENCE IF EXISTS dcl_07735_sequence;
CREATE SEQUENCE dcl_07735_sequence;
GRANT USAGE ON SEQUENCE dcl_07735_sequence TO CURRENT_USER;
GRANT USAGE ON SEQUENCE dcl_07735_sequence TO dcl_07735_grantor WITH GRANT OPTION;
SET ROLE dcl_07735_grantor;
REVOKE USAGE ON SEQUENCE dcl_07735_sequence FROM CURRENT_USER RESTRICT;
RESET ROLE;
SELECT has_sequence_privilege(CURRENT_USER, 'dcl_07735_sequence', 'USAGE');
RESET ROLE;
RESET ALL;
DROP SEQUENCE IF EXISTS dcl_07735_sequence;
DROP OWNED BY "dcl_07735_Grantee";
DROP OWNED BY dcl_07735_member;
DROP OWNED BY dcl_07735_grantor;
DROP ROLE IF EXISTS dcl_07735_member;
DROP ROLE IF EXISTS dcl_07735_grantor;
DROP ROLE IF EXISTS "dcl_07735_Grantee";
