-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_2 (column) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=current_user
-- factor grant_option_shape=inherit_or_set_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=missing_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=effect_query
-- factor cleanup_mode=reset_state
DROP TABLE IF EXISTS dcl_00676_table;
DROP ROLE IF EXISTS dcl_00676_grantor;
DROP ROLE IF EXISTS dcl_00676_member;
CREATE ROLE dcl_00676_grantor;
CREATE ROLE dcl_00676_member;
CREATE TABLE dcl_00676_table (id integer, payload text);
GRANT EXECUTE ON TABLE dcl_00676_missing_object TO dcl_00676_grantor WITH GRANT OPTION;
GRANT dcl_00676_grantor TO dcl_00676_member WITH SET TRUE;
SET ROLE dcl_00676_member;
SET ROLE dcl_00676_grantor;
GRANT EXECUTE ON TABLE dcl_00676_missing_object TO CURRENT_USER WITH INHERIT TRUE;
RESET ROLE;
SELECT count(*) AS privilege_effect_rows FROM dcl_00676_table;
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_00676_member;
DROP OWNED BY dcl_00676_grantor;
DROP ROLE IF EXISTS dcl_00676_member;
DROP ROLE IF EXISTS dcl_00676_grantor;
DROP TABLE IF EXISTS dcl_00676_table;
