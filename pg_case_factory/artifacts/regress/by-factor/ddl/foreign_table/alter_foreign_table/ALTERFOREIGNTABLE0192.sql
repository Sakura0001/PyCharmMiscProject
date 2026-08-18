-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-18
-- version      : 1.0
-- description  : ALTER FOREIGN TABLE no_type_usage_privilege=lacks_usage
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERFOREIGNTABLE0192
-- source_md: skills/pg-sql-generation/references/statements/ddl/foreign_table/alter_foreign_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/foreign_table/alter_foreign_table.yaml
-- primary_obligation_id: AFT-SFV|sfv-33d90682a3a038495b19177f|add_column
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterforeigntable_0192_base, alterforeigntable_0192_remote_table, alterforeigntable_0192_referenced_table, alterforeigntable_0192_fk_dependent, alterforeigntable_0192_fk_target, alterforeigntable_0192_partition_context, alterforeigntable_0192_partition_parent, alterforeigntable_0192_inheritance_parent, alterforeigntable_0192_child_marker, alterforeigntable_0192_parent_marker, alterforeigntable_0192_range_parent, alterforeigntable_0192_list_parent, alterforeigntable_0192_hash_parent, alterforeigntable_0192_row_table CASCADE;
\set ON_ERROR_STOP on
RESET ROLE;
DROP VIEW IF EXISTS alterforeigntable_0192_dependent_view CASCADE;
DROP VIEW IF EXISTS alterforeigntable_0192_whole_row_view CASCADE;
DROP MATERIALIZED VIEW IF EXISTS alterforeigntable_0192_dependent_matview CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_0192_source_schema CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_0192_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0192_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0192_zero_column_ft CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0192_remote_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0192_referenced_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0192_fk_dependent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0192_fk_target CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0192_partition_context CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0192_partition_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0192_inheritance_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0192_child_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0192_parent_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0192_range_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0192_list_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0192_hash_parent CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_0192_default_seq CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_0192_dependency_seq CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0192_default_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0192_dependency_fn(integer) CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0192_trigger_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0192_base_in(cstring) CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0192_base_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0192_mood CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0192_positive_integer CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0192_address CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0192_enum_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_0192_domain_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0192_composite_type CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0192_row_table CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0192_range_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0192_range_for_multi CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0192_multirange_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0192_array_element_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_0192_dependency_domain CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_0192_collation CASCADE;
DROP COLLATION IF EXISTS "alterforeigntable_0192_Mixed Collation" CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_0192_encoding_collation CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_0192_dependency_collation CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_0192_collation_schema CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_0192_target_schema CASCADE;
DROP ROLE IF EXISTS alterforeigntable_0192_actor;
DROP ROLE IF EXISTS alterforeigntable_0192_new_owner;
DROP SERVER IF EXISTS alterforeigntable_0192_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterforeigntable_0192_fdw CASCADE;
-- 2. 创建完整本地表、外表和因子专用夹具。
CREATE FOREIGN DATA WRAPPER alterforeigntable_0192_fdw NO HANDLER;
CREATE SERVER alterforeigntable_0192_server FOREIGN DATA WRAPPER alterforeigntable_0192_fdw;
CREATE TABLE alterforeigntable_0192_base (id bigint NOT NULL PRIMARY KEY, factor_col integer, drop_col text, base_col integer NOT NULL, period_col int4range NOT NULL, status smallint NOT NULL DEFAULT 0, payload varchar(128) NOT NULL DEFAULT '', CONSTRAINT alterforeigntable_0192_base_status_check CHECK (status BETWEEN 0 AND 9));
INSERT INTO alterforeigntable_0192_base (id, factor_col, drop_col, base_col, period_col, status, payload) VALUES (1, 1, 'drop-me', 2, int4range(1, 5), 1, 'baseline');
CREATE FOREIGN TABLE alterforeigntable_0192_ft (alterforeigntable_0192_id bigint NOT NULL, alterforeigntable_0192_factor_col integer OPTIONS (alterforeigntable_0192_existing_option_1 'old', alterforeigntable_0192_existing_option_2 'old'), alterforeigntable_0192_drop_col text, alterforeigntable_0192_base_col integer NOT NULL, alterforeigntable_0192_period_col int4range NOT NULL, alterforeigntable_0192_status smallint NOT NULL DEFAULT 0, alterforeigntable_0192_payload varchar(128) NOT NULL DEFAULT '', CONSTRAINT alterforeigntable_0192_base_check CHECK (alterforeigntable_0192_status BETWEEN 0 AND 9)) SERVER alterforeigntable_0192_server OPTIONS (alterforeigntable_0192_existing_option_1 'old', alterforeigntable_0192_existing_option_2 'old');
CREATE ROLE alterforeigntable_0192_actor NOLOGIN;
CREATE TYPE alterforeigntable_0192_enum_type AS ENUM ('one', 'two');
REVOKE USAGE ON TYPE alterforeigntable_0192_enum_type FROM PUBLIC;
ALTER FOREIGN TABLE alterforeigntable_0192_ft OWNER TO alterforeigntable_0192_actor;
SET ROLE alterforeigntable_0192_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER FOREIGN TABLE。
-- primary-target-begin
ALTER FOREIGN TABLE alterforeigntable_0192_ft ADD COLUMN alterforeigntable_0192_usage_probe alterforeigntable_0192_enum_type;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT 'no_type_usage_privilege'::text AS canonical_factor, 'lacks_usage'::text AS canonical_value;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_0192_New Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0192_renamed_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0192_target_schema.alterforeigntable_0192_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0192_source_schema.alterforeigntable_0192_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_0192_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0192_zero_column_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0192_ft CASCADE;
DROP VIEW IF EXISTS alterforeigntable_0192_dependent_view CASCADE;
DROP VIEW IF EXISTS alterforeigntable_0192_whole_row_view CASCADE;
DROP MATERIALIZED VIEW IF EXISTS alterforeigntable_0192_dependent_matview CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_0192_source_schema CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_0192_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0192_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0192_zero_column_ft CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0192_remote_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0192_referenced_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0192_fk_dependent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0192_fk_target CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0192_partition_context CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0192_partition_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0192_inheritance_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0192_child_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0192_parent_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0192_range_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0192_list_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0192_hash_parent CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_0192_default_seq CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_0192_dependency_seq CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0192_default_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0192_dependency_fn(integer) CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0192_trigger_fn() CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0192_base_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0192_mood CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0192_positive_integer CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0192_address CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0192_enum_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_0192_domain_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0192_composite_type CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0192_row_table CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0192_range_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0192_range_for_multi CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0192_multirange_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0192_array_element_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_0192_dependency_domain CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_0192_collation CASCADE;
DROP COLLATION IF EXISTS "alterforeigntable_0192_Mixed Collation" CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_0192_encoding_collation CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_0192_dependency_collation CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_0192_collation_schema CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_0192_target_schema CASCADE;
DROP ROLE IF EXISTS alterforeigntable_0192_actor;
DROP ROLE IF EXISTS alterforeigntable_0192_new_owner;
DROP SERVER IF EXISTS alterforeigntable_0192_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterforeigntable_0192_fdw CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0192_base, alterforeigntable_0192_remote_table, alterforeigntable_0192_referenced_table, alterforeigntable_0192_fk_dependent, alterforeigntable_0192_fk_target, alterforeigntable_0192_partition_context, alterforeigntable_0192_partition_parent, alterforeigntable_0192_inheritance_parent, alterforeigntable_0192_child_marker, alterforeigntable_0192_parent_marker, alterforeigntable_0192_range_parent, alterforeigntable_0192_list_parent, alterforeigntable_0192_hash_parent, alterforeigntable_0192_row_table CASCADE;
