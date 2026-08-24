-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_1 (table) with scope=parameter_privilege
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor privilege_scope=parameter_privilege
-- factor grantee_shape=current_role
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
DROP TABLE IF EXISTS dcl_07171_schema.dcl_07171_table;
DROP ROLE IF EXISTS dcl_07171_grantor;
DROP ROLE IF EXISTS dcl_07171_member;
CREATE ROLE dcl_07171_grantor;
CREATE ROLE dcl_07171_member;
DROP SCHEMA IF EXISTS dcl_07171_schema CASCADE;
CREATE SCHEMA dcl_07171_schema;
CREATE TABLE dcl_07171_schema.dcl_07171_table (id integer, payload text);
GRANT EXECUTE ON ALL TABLES IN SCHEMA dcl_07171_missing_object TO CURRENT_ROLE;
GRANT EXECUTE ON ALL TABLES IN SCHEMA dcl_07171_missing_object TO dcl_07171_grantor WITH GRANT OPTION;
GRANT dcl_07171_grantor TO dcl_07171_member WITH SET TRUE;
SET ROLE dcl_07171_member;
SET ROLE dcl_07171_grantor;
REVOKE EXECUTE ON ALL TABLES IN SCHEMA dcl_07171_missing_object FROM CURRENT_ROLE RESTRICT;
RESET ROLE;
SELECT count(*) AS table_count FROM dcl_07171_schema.dcl_07171_table;
RESET ROLE;
RESET ALL;
DROP SCHEMA IF EXISTS dcl_07171_schema CASCADE;
DROP OWNED BY dcl_07171_member;
DROP OWNED BY dcl_07171_grantor;
DROP ROLE IF EXISTS dcl_07171_member;
DROP ROLE IF EXISTS dcl_07171_grantor;
DROP TABLE IF EXISTS dcl_07171_schema.dcl_07171_table;
