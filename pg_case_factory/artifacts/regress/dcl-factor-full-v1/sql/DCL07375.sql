-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_2 (column) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
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
DROP TABLE IF EXISTS dcl_07375_schema.dcl_07375_table;
DROP ROLE IF EXISTS dcl_07375_grantor;
DROP ROLE IF EXISTS dcl_07375_member;
CREATE ROLE dcl_07375_grantor;
CREATE ROLE dcl_07375_member;
DROP SCHEMA IF EXISTS dcl_07375_schema CASCADE;
CREATE SCHEMA dcl_07375_schema;
CREATE TABLE dcl_07375_schema.dcl_07375_table (id integer, payload text);
GRANT EXECUTE ON TABLE dcl_07375_missing_object.dcl_07375_table TO PUBLIC;
GRANT EXECUTE ON TABLE dcl_07375_missing_object.dcl_07375_table TO dcl_07375_grantor WITH GRANT OPTION;
GRANT dcl_07375_grantor TO dcl_07375_member WITH SET TRUE;
SET ROLE dcl_07375_member;
SET ROLE dcl_07375_grantor;
REVOKE ADMIN OPTION FOR EXECUTE ON TABLE dcl_07375_missing_object.dcl_07375_table FROM PUBLIC RESTRICT;
RESET ROLE;
SELECT count(*) AS table_count FROM dcl_07375_schema.dcl_07375_table;
RESET ROLE;
RESET ALL;
DROP SCHEMA IF EXISTS dcl_07375_schema CASCADE;
DROP OWNED BY dcl_07375_member;
DROP OWNED BY dcl_07375_grantor;
DROP ROLE IF EXISTS dcl_07375_member;
DROP ROLE IF EXISTS dcl_07375_grantor;
DROP TABLE IF EXISTS dcl_07375_schema.dcl_07375_table;
