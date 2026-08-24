-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_14 (type) with scope=table_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_14
-- factor expected_status=failure
-- factor privilege_scope=table_privilege
-- factor grantee_shape=current_role
-- factor grant_option_shape=grant_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=schema_qualified
-- factor role_name_shape=missing_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=error_assertion
-- factor cleanup_mode=reset_state
DROP ROLE IF EXISTS dcl_05938_grantor;
DROP ROLE IF EXISTS dcl_05938_member;
CREATE ROLE dcl_05938_grantor;
CREATE ROLE dcl_05938_member;
DROP TYPE IF EXISTS dcl_05938_type;
CREATE TYPE dcl_05938_type AS ENUM ('alpha', 'beta');
GRANT USAGE ON TYPE dcl_05938_missing_object TO dcl_05938_grantor WITH GRANT OPTION;
GRANT dcl_05938_grantor TO dcl_05938_member WITH SET TRUE;
SET ROLE dcl_05938_member;
SET ROLE dcl_05938_grantor;
GRANT USAGE ON TYPE dcl_05938_missing_object TO CURRENT_ROLE WITH GRANT OPTION;
RESET ROLE;
SELECT 'expected_failure' AS expected_outcome, 'error_assertion' AS verification_mode;
RESET ROLE;
RESET ALL;
DROP TYPE IF EXISTS dcl_05938_type;
DROP OWNED BY dcl_05938_member;
DROP OWNED BY dcl_05938_grantor;
DROP ROLE IF EXISTS dcl_05938_member;
DROP ROLE IF EXISTS dcl_05938_grantor;
