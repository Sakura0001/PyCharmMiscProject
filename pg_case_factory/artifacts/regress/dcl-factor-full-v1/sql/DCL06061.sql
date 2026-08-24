-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_14 (type) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=current_role
-- factor grant_option_shape=admin_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=plain_identifier
-- factor role_name_shape=missing_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=returned_rows
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_06061_grantor;
DROP ROLE IF EXISTS dcl_06061_member;
CREATE ROLE dcl_06061_grantor;
CREATE ROLE dcl_06061_member;
DROP TYPE IF EXISTS dcl_06061_type;
CREATE TYPE dcl_06061_type AS ENUM ('alpha', 'beta');
GRANT USAGE ON TYPE dcl_06061_missing_object TO dcl_06061_grantor WITH GRANT OPTION;
GRANT dcl_06061_grantor TO dcl_06061_member WITH SET TRUE;
SET ROLE dcl_06061_member;
SET ROLE dcl_06061_grantor;
GRANT USAGE ON TYPE dcl_06061_missing_object TO CURRENT_ROLE WITH ADMIN OPTION;
RESET ROLE;
SELECT 'grant' AS completed_statement, 'schema_database_tablespace' AS privilege_scope;
RESET ROLE;
RESET ALL;
DROP TYPE IF EXISTS dcl_06061_type;
DROP OWNED BY dcl_06061_member;
DROP OWNED BY dcl_06061_grantor;
DROP ROLE IF EXISTS dcl_06061_member;
DROP ROLE IF EXISTS dcl_06061_grantor;
