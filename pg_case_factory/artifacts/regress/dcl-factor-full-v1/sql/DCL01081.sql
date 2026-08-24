-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_3 (sequence) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_3
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=role_name
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=missing_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=returned_rows
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_01081_grantor;
DROP ROLE IF EXISTS dcl_01081_member;
CREATE ROLE dcl_01081_grantor;
CREATE ROLE dcl_01081_member;
DROP SEQUENCE IF EXISTS dcl_01081_sequence;
CREATE SEQUENCE dcl_01081_sequence;
GRANT USAGE ON SEQUENCE dcl_01081_missing_object TO dcl_01081_grantor WITH GRANT OPTION;
GRANT dcl_01081_grantor TO dcl_01081_member WITH SET TRUE;
SET ROLE dcl_01081_member;
SET ROLE dcl_01081_grantor;
GRANT USAGE ON SEQUENCE dcl_01081_missing_object TO dcl_01081_missing_role;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'schema_database_tablespace' AS privilege_scope;
RESET ROLE;
RESET ALL;
DROP SEQUENCE IF EXISTS dcl_01081_sequence;
DROP OWNED BY dcl_01081_member;
DROP OWNED BY dcl_01081_grantor;
DROP ROLE IF EXISTS dcl_01081_member;
DROP ROLE IF EXISTS dcl_01081_grantor;
