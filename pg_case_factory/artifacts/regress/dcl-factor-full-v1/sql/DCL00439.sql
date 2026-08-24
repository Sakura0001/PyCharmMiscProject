-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 GRANT branch branch_1 (table) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
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
DROP TABLE IF EXISTS dcl_00439_schema.dcl_00439_table;
DROP ROLE IF EXISTS dcl_00439_grantor;
DROP ROLE IF EXISTS dcl_00439_member;
CREATE ROLE dcl_00439_grantor;
CREATE ROLE dcl_00439_member;
DROP SCHEMA IF EXISTS dcl_00439_schema CASCADE;
CREATE SCHEMA dcl_00439_schema;
CREATE TABLE dcl_00439_schema.dcl_00439_table (id integer, payload text);
GRANT EXECUTE ON ALL TABLES IN SCHEMA dcl_00439_missing_object TO dcl_00439_grantor WITH GRANT OPTION;
GRANT dcl_00439_grantor TO dcl_00439_member WITH SET TRUE;
SET ROLE dcl_00439_member;
SET ROLE dcl_00439_grantor;
GRANT EXECUTE ON ALL TABLES IN SCHEMA dcl_00439_missing_object TO PUBLIC WITH ADMIN OPTION;
RESET ROLE;
SELECT count(*) AS table_count FROM dcl_00439_schema.dcl_00439_table;
RESET ROLE;
RESET ALL;
DROP SCHEMA IF EXISTS dcl_00439_schema CASCADE;
DROP OWNED BY dcl_00439_member;
DROP OWNED BY dcl_00439_grantor;
DROP ROLE IF EXISTS dcl_00439_member;
DROP ROLE IF EXISTS dcl_00439_grantor;
DROP TABLE IF EXISTS dcl_00439_schema.dcl_00439_table;
