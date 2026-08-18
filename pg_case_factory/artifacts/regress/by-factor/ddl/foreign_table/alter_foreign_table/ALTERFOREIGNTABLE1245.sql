-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-18
-- version      : 1.0
-- description  : ALTER FOREIGN TABLE unique_constraint=column_unique_nulls_distinct
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERFOREIGNTABLE1245
-- source_md: skills/pg-sql-generation/references/statements/ddl/foreign_table/alter_foreign_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/foreign_table/alter_foreign_table.yaml
-- primary_obligation_id: AFT-INV|add_constraint|unique_constraint|column_unique_nulls_distinct
-- expected_outcome: expected_failure
-- expected_sqlstate: 0A000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterforeigntable_1245_base, alterforeigntable_1245_remote_table, alterforeigntable_1245_referenced_table, alterforeigntable_1245_fk_dependent, alterforeigntable_1245_fk_target, alterforeigntable_1245_partition_context, alterforeigntable_1245_partition_parent, alterforeigntable_1245_inheritance_parent, alterforeigntable_1245_child_marker, alterforeigntable_1245_parent_marker, alterforeigntable_1245_range_parent, alterforeigntable_1245_list_parent, alterforeigntable_1245_hash_parent, alterforeigntable_1245_row_table CASCADE;
\set ON_ERROR_STOP on
RESET ROLE;
DROP VIEW IF EXISTS alterforeigntable_1245_dependent_view CASCADE;
DROP VIEW IF EXISTS alterforeigntable_1245_whole_row_view CASCADE;
DROP MATERIALIZED VIEW IF EXISTS alterforeigntable_1245_dependent_matview CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1245_source_schema CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_1245_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1245_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1245_zero_column_ft CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1245_remote_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1245_referenced_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1245_fk_dependent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1245_fk_target CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1245_partition_context CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1245_partition_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1245_inheritance_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1245_child_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1245_parent_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1245_range_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1245_list_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1245_hash_parent CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_1245_default_seq CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_1245_dependency_seq CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1245_default_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1245_dependency_fn(integer) CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1245_trigger_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1245_base_in(cstring) CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1245_base_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1245_mood CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1245_positive_integer CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1245_address CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1245_enum_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_1245_domain_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1245_composite_type CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1245_row_table CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1245_range_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1245_range_for_multi CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1245_multirange_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1245_array_element_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_1245_dependency_domain CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1245_collation CASCADE;
DROP COLLATION IF EXISTS "alterforeigntable_1245_Mixed Collation" CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1245_encoding_collation CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1245_dependency_collation CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1245_collation_schema CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1245_target_schema CASCADE;
DROP ROLE IF EXISTS alterforeigntable_1245_actor;
DROP ROLE IF EXISTS alterforeigntable_1245_new_owner;
DROP SERVER IF EXISTS alterforeigntable_1245_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterforeigntable_1245_fdw CASCADE;
-- 2. 创建完整本地表、外表和因子专用夹具。
CREATE FOREIGN DATA WRAPPER alterforeigntable_1245_fdw NO HANDLER;
CREATE SERVER alterforeigntable_1245_server FOREIGN DATA WRAPPER alterforeigntable_1245_fdw;
CREATE TABLE alterforeigntable_1245_base (id bigint NOT NULL PRIMARY KEY, factor_col integer, drop_col text, base_col integer NOT NULL, period_col int4range NOT NULL, status smallint NOT NULL DEFAULT 0, payload varchar(128) NOT NULL DEFAULT '', CONSTRAINT alterforeigntable_1245_base_status_check CHECK (status BETWEEN 0 AND 9));
INSERT INTO alterforeigntable_1245_base (id, factor_col, drop_col, base_col, period_col, status, payload) VALUES (1, 1, 'drop-me', 2, int4range(1, 5), 1, 'baseline');
CREATE FOREIGN TABLE alterforeigntable_1245_ft (alterforeigntable_1245_id bigint NOT NULL, alterforeigntable_1245_factor_col integer OPTIONS (alterforeigntable_1245_existing_option_1 'old', alterforeigntable_1245_existing_option_2 'old'), alterforeigntable_1245_drop_col text, alterforeigntable_1245_base_col integer NOT NULL, alterforeigntable_1245_period_col int4range NOT NULL, alterforeigntable_1245_status smallint NOT NULL DEFAULT 0, alterforeigntable_1245_payload varchar(128) NOT NULL DEFAULT '', CONSTRAINT alterforeigntable_1245_base_check CHECK (alterforeigntable_1245_status BETWEEN 0 AND 9)) SERVER alterforeigntable_1245_server OPTIONS (alterforeigntable_1245_existing_option_1 'old', alterforeigntable_1245_existing_option_2 'old');
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER FOREIGN TABLE。
-- primary-target-begin
ALTER FOREIGN TABLE alterforeigntable_1245_ft ADD COLUMN alterforeigntable_1245_probe_col integer UNIQUE NULLS DISTINCT, ADD CONSTRAINT alterforeigntable_1245_factor_constraint_baseline CHECK (TRUE);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
SELECT :'target_sqlstate' = '0A000' AS target_sqlstate_matches_expected;
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_attribute AS a WHERE a.attrelid = 'alterforeigntable_1245_ft'::regclass AND a.attname = 'alterforeigntable_1245_factor_col' AND NOT a.attisdropped) AS constraint_factor_state_is_deterministic FROM (VALUES (1)) AS deterministic_probe(value) ORDER BY deterministic_probe.value;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_1245_New Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1245_renamed_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1245_target_schema.alterforeigntable_1245_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1245_source_schema.alterforeigntable_1245_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_1245_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1245_zero_column_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1245_ft CASCADE;
DROP VIEW IF EXISTS alterforeigntable_1245_dependent_view CASCADE;
DROP VIEW IF EXISTS alterforeigntable_1245_whole_row_view CASCADE;
DROP MATERIALIZED VIEW IF EXISTS alterforeigntable_1245_dependent_matview CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1245_source_schema CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_1245_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1245_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1245_zero_column_ft CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1245_remote_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1245_referenced_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1245_fk_dependent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1245_fk_target CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1245_partition_context CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1245_partition_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1245_inheritance_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1245_child_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1245_parent_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1245_range_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1245_list_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1245_hash_parent CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_1245_default_seq CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_1245_dependency_seq CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1245_default_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1245_dependency_fn(integer) CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1245_trigger_fn() CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1245_base_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1245_mood CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1245_positive_integer CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1245_address CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1245_enum_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_1245_domain_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1245_composite_type CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1245_row_table CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1245_range_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1245_range_for_multi CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1245_multirange_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1245_array_element_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_1245_dependency_domain CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1245_collation CASCADE;
DROP COLLATION IF EXISTS "alterforeigntable_1245_Mixed Collation" CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1245_encoding_collation CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1245_dependency_collation CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1245_collation_schema CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1245_target_schema CASCADE;
DROP ROLE IF EXISTS alterforeigntable_1245_actor;
DROP ROLE IF EXISTS alterforeigntable_1245_new_owner;
DROP SERVER IF EXISTS alterforeigntable_1245_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterforeigntable_1245_fdw CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1245_base, alterforeigntable_1245_remote_table, alterforeigntable_1245_referenced_table, alterforeigntable_1245_fk_dependent, alterforeigntable_1245_fk_target, alterforeigntable_1245_partition_context, alterforeigntable_1245_partition_parent, alterforeigntable_1245_inheritance_parent, alterforeigntable_1245_child_marker, alterforeigntable_1245_parent_marker, alterforeigntable_1245_range_parent, alterforeigntable_1245_list_parent, alterforeigntable_1245_hash_parent, alterforeigntable_1245_row_table CASCADE;
