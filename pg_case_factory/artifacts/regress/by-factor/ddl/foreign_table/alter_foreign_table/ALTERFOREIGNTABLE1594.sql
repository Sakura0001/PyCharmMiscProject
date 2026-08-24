-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-18
-- version      : 1.0
-- description  : ALTER FOREIGN TABLE dependency_state=generated_function_dependency
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERFOREIGNTABLE1594
-- source_md: skills/pg-sql-generation/references/statements/ddl/foreign_table/alter_foreign_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/foreign_table/alter_foreign_table.yaml
-- primary_obligation_id: AFT-INV|alter_column_type|dependency_state|generated_function_dependency
-- expected_outcome: expected_failure
-- expected_sqlstate: 0A000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterforeigntable_1594_base, alterforeigntable_1594_remote_table, alterforeigntable_1594_referenced_table, alterforeigntable_1594_fk_dependent, alterforeigntable_1594_fk_target, alterforeigntable_1594_partition_context, alterforeigntable_1594_partition_parent, alterforeigntable_1594_inheritance_parent, alterforeigntable_1594_child_marker, alterforeigntable_1594_parent_marker, alterforeigntable_1594_range_parent, alterforeigntable_1594_list_parent, alterforeigntable_1594_hash_parent, alterforeigntable_1594_row_table CASCADE;
\set ON_ERROR_STOP on
RESET ROLE;
DROP VIEW IF EXISTS alterforeigntable_1594_dependent_view CASCADE;
DROP VIEW IF EXISTS alterforeigntable_1594_whole_row_view CASCADE;
DROP MATERIALIZED VIEW IF EXISTS alterforeigntable_1594_dependent_matview CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1594_source_schema CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_1594_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1594_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1594_zero_column_ft CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1594_remote_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1594_referenced_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1594_fk_dependent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1594_fk_target CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1594_partition_context CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1594_partition_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1594_inheritance_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1594_child_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1594_parent_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1594_range_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1594_list_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1594_hash_parent CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_1594_default_seq CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_1594_dependency_seq CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1594_default_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1594_dependency_fn(integer) CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1594_trigger_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1594_base_in(cstring) CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1594_base_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1594_mood CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1594_positive_integer CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1594_address CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1594_enum_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_1594_domain_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1594_composite_type CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1594_row_table CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1594_range_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1594_range_for_multi CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1594_multirange_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1594_array_element_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_1594_dependency_domain CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1594_collation CASCADE;
DROP COLLATION IF EXISTS "alterforeigntable_1594_Mixed Collation" CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1594_encoding_collation CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1594_dependency_collation CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1594_collation_schema CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1594_target_schema CASCADE;
DROP ROLE IF EXISTS alterforeigntable_1594_actor;
DROP ROLE IF EXISTS alterforeigntable_1594_new_owner;
DROP SERVER IF EXISTS alterforeigntable_1594_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterforeigntable_1594_fdw CASCADE;
-- 2. 创建完整本地表、外表和因子专用夹具。
CREATE FOREIGN DATA WRAPPER alterforeigntable_1594_fdw NO HANDLER;
CREATE SERVER alterforeigntable_1594_server FOREIGN DATA WRAPPER alterforeigntable_1594_fdw;
CREATE TABLE alterforeigntable_1594_base (id bigint NOT NULL PRIMARY KEY, factor_col integer, drop_col text, base_col integer NOT NULL, period_col int4range NOT NULL, status smallint NOT NULL DEFAULT 0, payload varchar(128) NOT NULL DEFAULT '', CONSTRAINT alterforeigntable_1594_base_status_check CHECK (status BETWEEN 0 AND 9));
INSERT INTO alterforeigntable_1594_base (id, factor_col, drop_col, base_col, period_col, status, payload) VALUES (1, 1, 'drop-me', 2, int4range(1, 5), 1, 'baseline');
CREATE FOREIGN TABLE alterforeigntable_1594_ft (alterforeigntable_1594_id bigint NOT NULL, alterforeigntable_1594_factor_col integer OPTIONS (alterforeigntable_1594_existing_option_1 'old', alterforeigntable_1594_existing_option_2 'old'), alterforeigntable_1594_drop_col text, alterforeigntable_1594_base_col integer NOT NULL, alterforeigntable_1594_period_col int4range NOT NULL, alterforeigntable_1594_status smallint NOT NULL DEFAULT 0, alterforeigntable_1594_payload varchar(128) NOT NULL DEFAULT '', CONSTRAINT alterforeigntable_1594_base_check CHECK (alterforeigntable_1594_status BETWEEN 0 AND 9)) SERVER alterforeigntable_1594_server OPTIONS (alterforeigntable_1594_existing_option_1 'old', alterforeigntable_1594_existing_option_2 'old');
CREATE FUNCTION alterforeigntable_1594_dependency_fn(integer) RETURNS integer LANGUAGE sql IMMUTABLE STRICT AS 'SELECT $1 + 1';
ALTER FOREIGN TABLE alterforeigntable_1594_ft ADD COLUMN alterforeigntable_1594_generated_dep integer GENERATED ALWAYS AS (alterforeigntable_1594_dependency_fn(alterforeigntable_1594_factor_col)) STORED;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER FOREIGN TABLE。
-- primary-target-begin
ALTER FOREIGN TABLE alterforeigntable_1594_ft ALTER COLUMN alterforeigntable_1594_factor_col TYPE bigint;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
SELECT :'target_sqlstate' = '0A000' AS target_sqlstate_matches_expected;
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT 'generated_function_dependency'::text AS dependency_kind, true AS dependency_outcome_normalized;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_1594_New Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1594_renamed_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1594_target_schema.alterforeigntable_1594_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1594_source_schema.alterforeigntable_1594_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_1594_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1594_zero_column_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1594_ft CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1594_dependency_fn(integer) CASCADE;
DROP VIEW IF EXISTS alterforeigntable_1594_dependent_view CASCADE;
DROP VIEW IF EXISTS alterforeigntable_1594_whole_row_view CASCADE;
DROP MATERIALIZED VIEW IF EXISTS alterforeigntable_1594_dependent_matview CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1594_source_schema CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_1594_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1594_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1594_zero_column_ft CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1594_remote_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1594_referenced_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1594_fk_dependent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1594_fk_target CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1594_partition_context CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1594_partition_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1594_inheritance_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1594_child_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1594_parent_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1594_range_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1594_list_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1594_hash_parent CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_1594_default_seq CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_1594_dependency_seq CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1594_default_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1594_dependency_fn(integer) CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1594_trigger_fn() CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1594_base_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1594_mood CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1594_positive_integer CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1594_address CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1594_enum_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_1594_domain_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1594_composite_type CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1594_row_table CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1594_range_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1594_range_for_multi CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1594_multirange_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1594_array_element_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_1594_dependency_domain CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1594_collation CASCADE;
DROP COLLATION IF EXISTS "alterforeigntable_1594_Mixed Collation" CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1594_encoding_collation CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1594_dependency_collation CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1594_collation_schema CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1594_target_schema CASCADE;
DROP ROLE IF EXISTS alterforeigntable_1594_actor;
DROP ROLE IF EXISTS alterforeigntable_1594_new_owner;
DROP SERVER IF EXISTS alterforeigntable_1594_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterforeigntable_1594_fdw CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1594_base, alterforeigntable_1594_remote_table, alterforeigntable_1594_referenced_table, alterforeigntable_1594_fk_dependent, alterforeigntable_1594_fk_target, alterforeigntable_1594_partition_context, alterforeigntable_1594_partition_parent, alterforeigntable_1594_inheritance_parent, alterforeigntable_1594_child_marker, alterforeigntable_1594_parent_marker, alterforeigntable_1594_range_parent, alterforeigntable_1594_list_parent, alterforeigntable_1594_hash_parent, alterforeigntable_1594_row_table CASCADE;
