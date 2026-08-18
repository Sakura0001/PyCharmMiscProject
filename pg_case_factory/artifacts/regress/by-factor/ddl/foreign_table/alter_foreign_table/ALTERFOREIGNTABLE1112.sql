-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-18
-- version      : 1.0
-- description  : ALTER FOREIGN TABLE data_type_and_typmod=structured_config.user_defined_archetypes.values::multirange
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERFOREIGNTABLE1112
-- source_md: skills/pg-sql-generation/references/statements/ddl/foreign_table/alter_foreign_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/foreign_table/alter_foreign_table.yaml
-- primary_obligation_id: AFT-INV|alter_column_type|data_type_and_typmod|structured_config.user_defined_archetypes.values::multirange
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterforeigntable_1112_base, alterforeigntable_1112_remote_table, alterforeigntable_1112_referenced_table, alterforeigntable_1112_fk_dependent, alterforeigntable_1112_fk_target, alterforeigntable_1112_partition_context, alterforeigntable_1112_partition_parent, alterforeigntable_1112_inheritance_parent, alterforeigntable_1112_child_marker, alterforeigntable_1112_parent_marker, alterforeigntable_1112_range_parent, alterforeigntable_1112_list_parent, alterforeigntable_1112_hash_parent, alterforeigntable_1112_row_table CASCADE;
\set ON_ERROR_STOP on
RESET ROLE;
DROP VIEW IF EXISTS alterforeigntable_1112_dependent_view CASCADE;
DROP VIEW IF EXISTS alterforeigntable_1112_whole_row_view CASCADE;
DROP MATERIALIZED VIEW IF EXISTS alterforeigntable_1112_dependent_matview CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1112_source_schema CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_1112_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1112_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1112_zero_column_ft CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1112_remote_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1112_referenced_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1112_fk_dependent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1112_fk_target CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1112_partition_context CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1112_partition_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1112_inheritance_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1112_child_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1112_parent_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1112_range_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1112_list_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1112_hash_parent CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_1112_default_seq CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_1112_dependency_seq CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1112_default_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1112_dependency_fn(integer) CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1112_trigger_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1112_base_in(cstring) CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1112_base_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1112_mood CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1112_positive_integer CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1112_address CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1112_enum_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_1112_domain_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1112_composite_type CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1112_row_table CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1112_range_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1112_range_for_multi CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1112_multirange_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1112_array_element_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_1112_dependency_domain CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1112_collation CASCADE;
DROP COLLATION IF EXISTS "alterforeigntable_1112_Mixed Collation" CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1112_encoding_collation CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1112_dependency_collation CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1112_collation_schema CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1112_target_schema CASCADE;
DROP ROLE IF EXISTS alterforeigntable_1112_actor;
DROP ROLE IF EXISTS alterforeigntable_1112_new_owner;
DROP SERVER IF EXISTS alterforeigntable_1112_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterforeigntable_1112_fdw CASCADE;
-- 2. 创建完整本地表、外表和因子专用夹具。
CREATE FOREIGN DATA WRAPPER alterforeigntable_1112_fdw NO HANDLER;
CREATE SERVER alterforeigntable_1112_server FOREIGN DATA WRAPPER alterforeigntable_1112_fdw;
CREATE TABLE alterforeigntable_1112_base (id bigint NOT NULL PRIMARY KEY, factor_col integer, drop_col text, base_col integer NOT NULL, period_col int4range NOT NULL, status smallint NOT NULL DEFAULT 0, payload varchar(128) NOT NULL DEFAULT '', CONSTRAINT alterforeigntable_1112_base_status_check CHECK (status BETWEEN 0 AND 9));
INSERT INTO alterforeigntable_1112_base (id, factor_col, drop_col, base_col, period_col, status, payload) VALUES (1, 1, 'drop-me', 2, int4range(1, 5), 1, 'baseline');
CREATE FOREIGN TABLE alterforeigntable_1112_ft (alterforeigntable_1112_id bigint NOT NULL, alterforeigntable_1112_factor_col integer OPTIONS (alterforeigntable_1112_existing_option_1 'old', alterforeigntable_1112_existing_option_2 'old'), alterforeigntable_1112_drop_col text, alterforeigntable_1112_base_col integer NOT NULL, alterforeigntable_1112_period_col int4range NOT NULL, alterforeigntable_1112_status smallint NOT NULL DEFAULT 0, alterforeigntable_1112_payload varchar(128) NOT NULL DEFAULT '', CONSTRAINT alterforeigntable_1112_base_check CHECK (alterforeigntable_1112_status BETWEEN 0 AND 9)) SERVER alterforeigntable_1112_server OPTIONS (alterforeigntable_1112_existing_option_1 'old', alterforeigntable_1112_existing_option_2 'old');
CREATE TYPE alterforeigntable_1112_range_for_multi AS RANGE (SUBTYPE=integer, MULTIRANGE_TYPE_NAME=alterforeigntable_1112_multirange_type);
-- 3. 执行唯一获得覆盖信用的 ALTER FOREIGN TABLE。
-- primary-target-begin
ALTER FOREIGN TABLE alterforeigntable_1112_ft ALTER COLUMN alterforeigntable_1112_factor_col TYPE alterforeigntable_1112_multirange_type;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_attribute AS a WHERE a.attrelid = 'alterforeigntable_1112_ft'::regclass AND a.attname = 'alterforeigntable_1112_factor_col' AND NOT a.attisdropped) AS type_factor_applied FROM (VALUES (1)) AS deterministic_probe(value) ORDER BY deterministic_probe.value;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_1112_New Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1112_renamed_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1112_target_schema.alterforeigntable_1112_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1112_source_schema.alterforeigntable_1112_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_1112_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1112_zero_column_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1112_ft CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1112_range_for_multi CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1112_multirange_type CASCADE;
DROP VIEW IF EXISTS alterforeigntable_1112_dependent_view CASCADE;
DROP VIEW IF EXISTS alterforeigntable_1112_whole_row_view CASCADE;
DROP MATERIALIZED VIEW IF EXISTS alterforeigntable_1112_dependent_matview CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1112_source_schema CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_1112_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1112_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1112_zero_column_ft CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1112_remote_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1112_referenced_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1112_fk_dependent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1112_fk_target CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1112_partition_context CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1112_partition_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1112_inheritance_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1112_child_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1112_parent_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1112_range_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1112_list_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1112_hash_parent CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_1112_default_seq CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_1112_dependency_seq CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1112_default_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1112_dependency_fn(integer) CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1112_trigger_fn() CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1112_base_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1112_mood CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1112_positive_integer CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1112_address CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1112_enum_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_1112_domain_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1112_composite_type CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1112_row_table CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1112_range_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1112_range_for_multi CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1112_multirange_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1112_array_element_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_1112_dependency_domain CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1112_collation CASCADE;
DROP COLLATION IF EXISTS "alterforeigntable_1112_Mixed Collation" CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1112_encoding_collation CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1112_dependency_collation CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1112_collation_schema CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1112_target_schema CASCADE;
DROP ROLE IF EXISTS alterforeigntable_1112_actor;
DROP ROLE IF EXISTS alterforeigntable_1112_new_owner;
DROP SERVER IF EXISTS alterforeigntable_1112_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterforeigntable_1112_fdw CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1112_base, alterforeigntable_1112_remote_table, alterforeigntable_1112_referenced_table, alterforeigntable_1112_fk_dependent, alterforeigntable_1112_fk_target, alterforeigntable_1112_partition_context, alterforeigntable_1112_partition_parent, alterforeigntable_1112_inheritance_parent, alterforeigntable_1112_child_marker, alterforeigntable_1112_parent_marker, alterforeigntable_1112_range_parent, alterforeigntable_1112_list_parent, alterforeigntable_1112_hash_parent, alterforeigntable_1112_row_table CASCADE;
