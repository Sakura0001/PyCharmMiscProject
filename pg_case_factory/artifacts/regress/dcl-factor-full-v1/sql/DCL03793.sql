-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_9 (language) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_9
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=public
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
DROP ROLE IF EXISTS dcl_03793_grantor;
DROP ROLE IF EXISTS dcl_03793_member;
CREATE ROLE dcl_03793_grantor;
CREATE ROLE dcl_03793_member;
GRANT USAGE ON LANGUAGE plpgsql TO dcl_03793_grantor WITH GRANT OPTION;
GRANT dcl_03793_grantor TO dcl_03793_member WITH SET TRUE;
SET ROLE dcl_03793_member;
SET ROLE dcl_03793_grantor;
GRANT USAGE ON LANGUAGE plpgsql TO PUBLIC;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'schema_database_tablespace' AS privilege_scope;
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_03793_member;
DROP OWNED BY dcl_03793_grantor;
DROP ROLE IF EXISTS dcl_03793_member;
DROP ROLE IF EXISTS dcl_03793_grantor;
