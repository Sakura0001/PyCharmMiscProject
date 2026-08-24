-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_2 (column) with scope=schema_database_tablespace
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=failure
-- factor privilege_scope=schema_database_tablespace
-- factor grantee_shape=public
-- factor grant_option_shape=admin_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=missing_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP TABLE IF EXISTS dcl_07435_schema.dcl_07435_table;
DROP ROLE IF EXISTS dcl_07435_grantor;
DROP ROLE IF EXISTS dcl_07435_member;
CREATE ROLE dcl_07435_grantor;
CREATE ROLE dcl_07435_member;
DROP SCHEMA IF EXISTS dcl_07435_schema CASCADE;
CREATE SCHEMA dcl_07435_schema;
CREATE TABLE dcl_07435_schema.dcl_07435_table (id integer, payload text);
GRANT EXECUTE ON TABLE dcl_07435_missing_object.dcl_07435_table TO PUBLIC;
GRANT EXECUTE ON TABLE dcl_07435_missing_object.dcl_07435_table TO dcl_07435_grantor WITH GRANT OPTION;
GRANT dcl_07435_grantor TO dcl_07435_member WITH SET TRUE;
SET ROLE dcl_07435_member;
SET ROLE dcl_07435_grantor;
REVOKE ADMIN OPTION FOR EXECUTE ON TABLE dcl_07435_missing_object.dcl_07435_table FROM PUBLIC RESTRICT;
RESET ROLE;
SELECT count(*) AS table_count FROM dcl_07435_schema.dcl_07435_table;
RESET ROLE;
RESET ALL;
DROP SCHEMA IF EXISTS dcl_07435_schema CASCADE;
DROP OWNED BY dcl_07435_member;
DROP OWNED BY dcl_07435_grantor;
DROP ROLE IF EXISTS dcl_07435_member;
DROP ROLE IF EXISTS dcl_07435_grantor;
DROP TABLE IF EXISTS dcl_07435_schema.dcl_07435_table;
