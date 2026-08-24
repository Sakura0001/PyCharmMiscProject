-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 REVOKE branch branch_2 (column) with scope=table_maintain
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_2
-- factor expected_status=failure
-- factor privilege_scope=table_maintain
-- factor grantee_shape=role_name
-- factor grant_option_shape=grant_option
-- factor grantor_shape=implicit_owner
-- factor object_name_shape=missing_object
-- factor role_name_shape=missing_role
-- factor dependency_state=missing_dependency
-- factor privilege_context=owner
-- factor invalid_combination=object_type_mismatch
-- factor ownership_boundary=member_role
-- factor verification_mode=effect_query
-- factor cleanup_mode=reset_state
DROP TABLE IF EXISTS dcl_07660_table;
DROP ROLE IF EXISTS dcl_07660_grantor;
DROP ROLE IF EXISTS dcl_07660_member;
CREATE ROLE dcl_07660_grantor;
CREATE ROLE dcl_07660_member;
CREATE TABLE dcl_07660_table (id integer, payload text);
GRANT EXECUTE ON TABLE dcl_07660_missing_object TO dcl_07660_missing_role;
GRANT EXECUTE ON TABLE dcl_07660_missing_object TO dcl_07660_grantor WITH GRANT OPTION;
GRANT dcl_07660_grantor TO dcl_07660_member WITH SET TRUE;
SET ROLE dcl_07660_member;
SET ROLE dcl_07660_grantor;
REVOKE GRANT OPTION FOR EXECUTE ON TABLE dcl_07660_missing_object FROM dcl_07660_missing_role RESTRICT;
RESET ROLE;
SET ROLE dcl_07660_missing_role;
SELECT count(*) AS privilege_effect_rows FROM dcl_07660_table;
RESET ROLE;
RESET ROLE;
RESET ALL;
DROP OWNED BY dcl_07660_member;
DROP OWNED BY dcl_07660_grantor;
DROP ROLE IF EXISTS dcl_07660_member;
DROP ROLE IF EXISTS dcl_07660_grantor;
DROP TABLE IF EXISTS dcl_07660_table;
