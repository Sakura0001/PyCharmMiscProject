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
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=quoted_role
-- factor dependency_state=ready
-- factor privilege_context=granted_role
-- factor invalid_combination=none
-- factor ownership_boundary=member_role
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS "dcl_00931_Grantee";
DROP ROLE IF EXISTS dcl_00931_grantor;
DROP ROLE IF EXISTS dcl_00931_member;
CREATE ROLE "dcl_00931_Grantee";
CREATE ROLE dcl_00931_grantor;
CREATE ROLE dcl_00931_member;
DROP SEQUENCE IF EXISTS dcl_00931_sequence;
CREATE SEQUENCE dcl_00931_sequence;
GRANT USAGE ON SEQUENCE dcl_00931_sequence TO dcl_00931_grantor WITH GRANT OPTION;
SET ROLE dcl_00931_grantor;
GRANT USAGE ON SEQUENCE dcl_00931_sequence TO "dcl_00931_Grantee";
RESET ROLE;
SELECT has_sequence_privilege(CURRENT_USER, 'dcl_00931_sequence', 'USAGE');
RESET ROLE;
RESET ALL;
DROP SEQUENCE IF EXISTS dcl_00931_sequence;
DROP OWNED BY "dcl_00931_Grantee";
DROP OWNED BY dcl_00931_member;
DROP OWNED BY dcl_00931_grantor;
DROP ROLE IF EXISTS dcl_00931_member;
DROP ROLE IF EXISTS dcl_00931_grantor;
DROP ROLE IF EXISTS "dcl_00931_Grantee";
