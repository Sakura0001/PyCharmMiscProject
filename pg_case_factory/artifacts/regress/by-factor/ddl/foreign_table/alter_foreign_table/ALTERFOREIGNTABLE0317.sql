-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-18
-- version      : 1.0
-- description  : ALTER FOREIGN TABLE column_name_shape=identifier_exactly_63_bytes
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERFOREIGNTABLE0317
-- source_md: skills/pg-sql-generation/references/statements/ddl/foreign_table/alter_foreign_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/foreign_table/alter_foreign_table.yaml
-- primary_obligation_id: AFT-INV|column_options|column_name_shape|identifier_exactly_63_bytes
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterforeigntable_0317_base, alterforeigntable_0317_remote_table, alterforeigntable_0317_referenced_table, alterforeigntable_0317_fk_dependent, alterforeigntable_0317_fk_target, alterforeigntable_0317_partition_context, alterforeigntable_0317_partition_parent, alterforeigntable_0317_inheritance_parent, alterforeigntable_0317_child_marker, alterforeigntable_0317_parent_marker, alterforeigntable_0317_range_parent, alterforeigntable_0317_list_parent, alterforeigntable_0317_hash_parent, alterforeigntable_0317_row_table CASCADE;
\set ON_ERROR_STOP on
RESET ROLE;
DROP VIEW IF EXISTS alterforeigntable_0317_dependent_view CASCADE;
DROP VIEW IF EXISTS alterforeigntable_0317_whole_row_view CASCADE;
DROP MATERIALIZED VIEW IF EXISTS alterforeigntable_0317_dependent_matview CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_0317_source_schema CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_0317_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0317_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0317_zero_column_ft CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0317_remote_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0317_referenced_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0317_fk_dependent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0317_fk_target CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0317_partition_context CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0317_partition_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0317_inheritance_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0317_child_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0317_parent_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0317_range_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0317_list_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0317_hash_parent CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_0317_default_seq CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_0317_dependency_seq CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0317_default_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0317_dependency_fn(integer) CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0317_trigger_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0317_base_in(cstring) CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0317_base_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0317_mood CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0317_positive_integer CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0317_address CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0317_enum_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_0317_domain_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0317_composite_type CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0317_row_table CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0317_range_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0317_range_for_multi CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0317_multirange_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0317_array_element_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_0317_dependency_domain CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_0317_collation CASCADE;
DROP COLLATION IF EXISTS "alterforeigntable_0317_Mixed Collation" CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_0317_encoding_collation CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_0317_dependency_collation CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_0317_collation_schema CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_0317_target_schema CASCADE;
DROP ROLE IF EXISTS alterforeigntable_0317_actor;
DROP ROLE IF EXISTS alterforeigntable_0317_new_owner;
DROP SERVER IF EXISTS alterforeigntable_0317_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterforeigntable_0317_fdw CASCADE;
-- 2. 创建完整本地表、外表和因子专用夹具。
CREATE FOREIGN DATA WRAPPER alterforeigntable_0317_fdw NO HANDLER;
CREATE SERVER alterforeigntable_0317_server FOREIGN DATA WRAPPER alterforeigntable_0317_fdw;
CREATE TABLE alterforeigntable_0317_base (id bigint NOT NULL PRIMARY KEY, factor_col integer, drop_col text, base_col integer NOT NULL, period_col int4range NOT NULL, status smallint NOT NULL DEFAULT 0, payload varchar(128) NOT NULL DEFAULT '', CONSTRAINT alterforeigntable_0317_base_status_check CHECK (status BETWEEN 0 AND 9));
INSERT INTO alterforeigntable_0317_base (id, factor_col, drop_col, base_col, period_col, status, payload) VALUES (1, 1, 'drop-me', 2, int4range(1, 5), 1, 'baseline');
CREATE FOREIGN TABLE alterforeigntable_0317_ft (alterforeigntable_0317_id bigint NOT NULL, alterforeigntable_0317_factor_col integer OPTIONS (alterforeigntable_0317_existing_option_1 'old', alterforeigntable_0317_existing_option_2 'old'), alterforeigntable_0317_drop_col text, alterforeigntable_0317_base_col integer NOT NULL, alterforeigntable_0317_period_col int4range NOT NULL, alterforeigntable_0317_status smallint NOT NULL DEFAULT 0, alterforeigntable_0317_payload varchar(128) NOT NULL DEFAULT '', CONSTRAINT alterforeigntable_0317_base_check CHECK (alterforeigntable_0317_status BETWEEN 0 AND 9)) SERVER alterforeigntable_0317_server OPTIONS (alterforeigntable_0317_existing_option_1 'old', alterforeigntable_0317_existing_option_2 'old');
ALTER FOREIGN TABLE alterforeigntable_0317_ft RENAME COLUMN alterforeigntable_0317_factor_col TO ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc;
-- 3. 执行唯一获得覆盖信用的 ALTER FOREIGN TABLE。
-- primary-target-begin
ALTER FOREIGN TABLE alterforeigntable_0317_ft ALTER COLUMN ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc OPTIONS (ADD alterforeigntable_0317_factor_option 'enabled');
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_attribute AS a WHERE a.attrelid = 'alterforeigntable_0317_ft'::regclass AND a.attname = 'ccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc' AND NOT a.attisdropped) AS column_name_normalized FROM (VALUES (1)) AS deterministic_probe(value) ORDER BY deterministic_probe.value;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_0317_New Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0317_renamed_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0317_target_schema.alterforeigntable_0317_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0317_source_schema.alterforeigntable_0317_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_0317_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0317_zero_column_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0317_ft CASCADE;
DROP VIEW IF EXISTS alterforeigntable_0317_dependent_view CASCADE;
DROP VIEW IF EXISTS alterforeigntable_0317_whole_row_view CASCADE;
DROP MATERIALIZED VIEW IF EXISTS alterforeigntable_0317_dependent_matview CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_0317_source_schema CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_0317_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0317_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0317_zero_column_ft CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0317_remote_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0317_referenced_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0317_fk_dependent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0317_fk_target CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0317_partition_context CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0317_partition_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0317_inheritance_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0317_child_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0317_parent_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0317_range_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0317_list_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0317_hash_parent CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_0317_default_seq CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_0317_dependency_seq CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0317_default_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0317_dependency_fn(integer) CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0317_trigger_fn() CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0317_base_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0317_mood CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0317_positive_integer CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0317_address CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0317_enum_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_0317_domain_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0317_composite_type CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0317_row_table CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0317_range_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0317_range_for_multi CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0317_multirange_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0317_array_element_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_0317_dependency_domain CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_0317_collation CASCADE;
DROP COLLATION IF EXISTS "alterforeigntable_0317_Mixed Collation" CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_0317_encoding_collation CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_0317_dependency_collation CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_0317_collation_schema CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_0317_target_schema CASCADE;
DROP ROLE IF EXISTS alterforeigntable_0317_actor;
DROP ROLE IF EXISTS alterforeigntable_0317_new_owner;
DROP SERVER IF EXISTS alterforeigntable_0317_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterforeigntable_0317_fdw CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0317_base, alterforeigntable_0317_remote_table, alterforeigntable_0317_referenced_table, alterforeigntable_0317_fk_dependent, alterforeigntable_0317_fk_target, alterforeigntable_0317_partition_context, alterforeigntable_0317_partition_parent, alterforeigntable_0317_inheritance_parent, alterforeigntable_0317_child_marker, alterforeigntable_0317_parent_marker, alterforeigntable_0317_range_parent, alterforeigntable_0317_list_parent, alterforeigntable_0317_hash_parent, alterforeigntable_0317_row_table CASCADE;
