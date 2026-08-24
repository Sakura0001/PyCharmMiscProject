-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_2 (column) with scope=column_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=failure
-- factor privilege_scope=column_privilege
-- factor grantee_shape=role_name
-- factor grant_option_shape=absent
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=all_objects_in_schema
-- factor role_name_shape=missing_role
-- factor dependency_state=ready
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=catalog_query
-- factor cleanup_mode=reset_state
DROP TABLE IF EXISTS dcl_00571_schema.dcl_00571_table;
DROP ROLE IF EXISTS dcl_00571_grantor;
DROP ROLE IF EXISTS dcl_00571_member;
CREATE ROLE dcl_00571_grantor;
CREATE ROLE dcl_00571_member;
DROP SCHEMA IF EXISTS dcl_00571_schema CASCADE;
CREATE SCHEMA dcl_00571_schema;
CREATE TABLE dcl_00571_schema.dcl_00571_table (id integer, payload text);
GRANT EXECUTE ON TABLE dcl_00571_missing_object.dcl_00571_table TO dcl_00571_grantor WITH GRANT OPTION;
GRANT dcl_00571_grantor TO dcl_00571_member WITH SET TRUE;
SET ROLE dcl_00571_member;
SET ROLE dcl_00571_grantor;
GRANT EXECUTE ON TABLE dcl_00571_missing_object.dcl_00571_table TO dcl_00571_missing_role;
RESET ROLE;
SELECT count(*) AS table_count FROM dcl_00571_schema.dcl_00571_table;
RESET ROLE;
RESET ALL;
DROP SCHEMA IF EXISTS dcl_00571_schema CASCADE;
DROP OWNED BY dcl_00571_member;
DROP OWNED BY dcl_00571_grantor;
DROP ROLE IF EXISTS dcl_00571_member;
DROP ROLE IF EXISTS dcl_00571_grantor;
DROP TABLE IF EXISTS dcl_00571_schema.dcl_00571_table;
