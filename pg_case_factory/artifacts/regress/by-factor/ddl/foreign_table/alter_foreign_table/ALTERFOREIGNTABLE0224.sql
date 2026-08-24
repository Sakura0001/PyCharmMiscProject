-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-18
-- version      : 1.0
-- description  : ALTER FOREIGN TABLE set_role_capability=cannot_set_role
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERFOREIGNTABLE0224
-- source_md: skills/pg-sql-generation/references/statements/ddl/foreign_table/alter_foreign_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/foreign_table/alter_foreign_table.yaml
-- primary_obligation_id: AFT-SFV|sfv-ecfcb8bde3ff2d8f79c691a3|owner
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterforeigntable_0224_base, alterforeigntable_0224_remote_table, alterforeigntable_0224_referenced_table, alterforeigntable_0224_fk_dependent, alterforeigntable_0224_fk_target, alterforeigntable_0224_partition_context, alterforeigntable_0224_partition_parent, alterforeigntable_0224_inheritance_parent, alterforeigntable_0224_child_marker, alterforeigntable_0224_parent_marker, alterforeigntable_0224_range_parent, alterforeigntable_0224_list_parent, alterforeigntable_0224_hash_parent, alterforeigntable_0224_row_table CASCADE;
\set ON_ERROR_STOP on
RESET ROLE;
DROP VIEW IF EXISTS alterforeigntable_0224_dependent_view CASCADE;
DROP VIEW IF EXISTS alterforeigntable_0224_whole_row_view CASCADE;
DROP MATERIALIZED VIEW IF EXISTS alterforeigntable_0224_dependent_matview CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_0224_source_schema CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_0224_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0224_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0224_zero_column_ft CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0224_remote_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0224_referenced_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0224_fk_dependent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0224_fk_target CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0224_partition_context CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0224_partition_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0224_inheritance_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0224_child_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0224_parent_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0224_range_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0224_list_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0224_hash_parent CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_0224_default_seq CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_0224_dependency_seq CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0224_default_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0224_dependency_fn(integer) CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0224_trigger_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0224_base_in(cstring) CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0224_base_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0224_mood CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0224_positive_integer CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0224_address CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0224_enum_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_0224_domain_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0224_composite_type CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0224_row_table CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0224_range_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0224_range_for_multi CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0224_multirange_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0224_array_element_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_0224_dependency_domain CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_0224_collation CASCADE;
DROP COLLATION IF EXISTS "alterforeigntable_0224_Mixed Collation" CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_0224_encoding_collation CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_0224_dependency_collation CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_0224_collation_schema CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_0224_target_schema CASCADE;
DROP ROLE IF EXISTS alterforeigntable_0224_actor;
DROP ROLE IF EXISTS alterforeigntable_0224_new_owner;
DROP SERVER IF EXISTS alterforeigntable_0224_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterforeigntable_0224_fdw CASCADE;
-- 2. 创建完整本地表、外表和因子专用夹具。
CREATE FOREIGN DATA WRAPPER alterforeigntable_0224_fdw NO HANDLER;
CREATE SERVER alterforeigntable_0224_server FOREIGN DATA WRAPPER alterforeigntable_0224_fdw;
CREATE TABLE alterforeigntable_0224_base (id bigint NOT NULL PRIMARY KEY, factor_col integer, drop_col text, base_col integer NOT NULL, period_col int4range NOT NULL, status smallint NOT NULL DEFAULT 0, payload varchar(128) NOT NULL DEFAULT '', CONSTRAINT alterforeigntable_0224_base_status_check CHECK (status BETWEEN 0 AND 9));
INSERT INTO alterforeigntable_0224_base (id, factor_col, drop_col, base_col, period_col, status, payload) VALUES (1, 1, 'drop-me', 2, int4range(1, 5), 1, 'baseline');
CREATE ROLE alterforeigntable_0224_new_owner NOLOGIN;
CREATE FOREIGN TABLE alterforeigntable_0224_ft (alterforeigntable_0224_id bigint NOT NULL, alterforeigntable_0224_factor_col integer OPTIONS (alterforeigntable_0224_existing_option_1 'old', alterforeigntable_0224_existing_option_2 'old'), alterforeigntable_0224_drop_col text, alterforeigntable_0224_base_col integer NOT NULL, alterforeigntable_0224_period_col int4range NOT NULL, alterforeigntable_0224_status smallint NOT NULL DEFAULT 0, alterforeigntable_0224_payload varchar(128) NOT NULL DEFAULT '', CONSTRAINT alterforeigntable_0224_base_check CHECK (alterforeigntable_0224_status BETWEEN 0 AND 9)) SERVER alterforeigntable_0224_server OPTIONS (alterforeigntable_0224_existing_option_1 'old', alterforeigntable_0224_existing_option_2 'old');
CREATE ROLE alterforeigntable_0224_actor NOLOGIN;
ALTER FOREIGN TABLE alterforeigntable_0224_ft OWNER TO alterforeigntable_0224_actor;
GRANT CREATE ON SCHEMA public TO alterforeigntable_0224_new_owner;
SET ROLE alterforeigntable_0224_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER FOREIGN TABLE。
-- primary-target-begin
ALTER FOREIGN TABLE alterforeigntable_0224_ft OWNER TO alterforeigntable_0224_new_owner;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT 'set_role_capability'::text AS canonical_factor, 'cannot_set_role'::text AS canonical_value;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_0224_New Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0224_renamed_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0224_target_schema.alterforeigntable_0224_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0224_source_schema.alterforeigntable_0224_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_0224_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0224_zero_column_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0224_ft CASCADE;
DO $pgcf$ BEGIN IF EXISTS (SELECT 1 FROM pg_catalog.pg_roles WHERE rolname = 'alterforeigntable_0224_new_owner') THEN EXECUTE 'REVOKE CREATE ON SCHEMA public FROM alterforeigntable_0224_new_owner'; END IF; END $pgcf$;
DROP VIEW IF EXISTS alterforeigntable_0224_dependent_view CASCADE;
DROP VIEW IF EXISTS alterforeigntable_0224_whole_row_view CASCADE;
DROP MATERIALIZED VIEW IF EXISTS alterforeigntable_0224_dependent_matview CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_0224_source_schema CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_0224_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0224_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0224_zero_column_ft CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0224_remote_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0224_referenced_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0224_fk_dependent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0224_fk_target CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0224_partition_context CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0224_partition_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0224_inheritance_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0224_child_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0224_parent_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0224_range_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0224_list_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0224_hash_parent CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_0224_default_seq CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_0224_dependency_seq CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0224_default_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0224_dependency_fn(integer) CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0224_trigger_fn() CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0224_base_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0224_mood CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0224_positive_integer CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0224_address CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0224_enum_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_0224_domain_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0224_composite_type CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0224_row_table CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0224_range_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0224_range_for_multi CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0224_multirange_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0224_array_element_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_0224_dependency_domain CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_0224_collation CASCADE;
DROP COLLATION IF EXISTS "alterforeigntable_0224_Mixed Collation" CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_0224_encoding_collation CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_0224_dependency_collation CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_0224_collation_schema CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_0224_target_schema CASCADE;
DROP ROLE IF EXISTS alterforeigntable_0224_actor;
DROP ROLE IF EXISTS alterforeigntable_0224_new_owner;
DROP SERVER IF EXISTS alterforeigntable_0224_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterforeigntable_0224_fdw CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0224_base, alterforeigntable_0224_remote_table, alterforeigntable_0224_referenced_table, alterforeigntable_0224_fk_dependent, alterforeigntable_0224_fk_target, alterforeigntable_0224_partition_context, alterforeigntable_0224_partition_parent, alterforeigntable_0224_inheritance_parent, alterforeigntable_0224_child_marker, alterforeigntable_0224_parent_marker, alterforeigntable_0224_range_parent, alterforeigntable_0224_list_parent, alterforeigntable_0224_hash_parent, alterforeigntable_0224_row_table CASCADE;
