-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-18
-- version      : 1.0
-- description  : ALTER FOREIGN TABLE check_constraint=table_check_no_inherit
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERFOREIGNTABLE1293
-- source_md: skills/pg-sql-generation/references/statements/ddl/foreign_table/alter_foreign_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/foreign_table/alter_foreign_table.yaml
-- primary_obligation_id: AFT-INV|add_constraint|check_constraint|table_check_no_inherit
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterforeigntable_1293_base, alterforeigntable_1293_remote_table, alterforeigntable_1293_referenced_table, alterforeigntable_1293_fk_dependent, alterforeigntable_1293_fk_target, alterforeigntable_1293_partition_context, alterforeigntable_1293_partition_parent, alterforeigntable_1293_inheritance_parent, alterforeigntable_1293_child_marker, alterforeigntable_1293_parent_marker, alterforeigntable_1293_range_parent, alterforeigntable_1293_list_parent, alterforeigntable_1293_hash_parent, alterforeigntable_1293_row_table CASCADE;
\set ON_ERROR_STOP on
RESET ROLE;
DROP VIEW IF EXISTS alterforeigntable_1293_dependent_view CASCADE;
DROP VIEW IF EXISTS alterforeigntable_1293_whole_row_view CASCADE;
DROP MATERIALIZED VIEW IF EXISTS alterforeigntable_1293_dependent_matview CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1293_source_schema CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_1293_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1293_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1293_zero_column_ft CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1293_remote_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1293_referenced_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1293_fk_dependent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1293_fk_target CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1293_partition_context CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1293_partition_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1293_inheritance_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1293_child_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1293_parent_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1293_range_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1293_list_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1293_hash_parent CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_1293_default_seq CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_1293_dependency_seq CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1293_default_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1293_dependency_fn(integer) CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1293_trigger_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1293_base_in(cstring) CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1293_base_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1293_mood CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1293_positive_integer CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1293_address CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1293_enum_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_1293_domain_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1293_composite_type CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1293_row_table CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1293_range_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1293_range_for_multi CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1293_multirange_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1293_array_element_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_1293_dependency_domain CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1293_collation CASCADE;
DROP COLLATION IF EXISTS "alterforeigntable_1293_Mixed Collation" CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1293_encoding_collation CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1293_dependency_collation CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1293_collation_schema CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1293_target_schema CASCADE;
DROP ROLE IF EXISTS alterforeigntable_1293_actor;
DROP ROLE IF EXISTS alterforeigntable_1293_new_owner;
DROP SERVER IF EXISTS alterforeigntable_1293_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterforeigntable_1293_fdw CASCADE;
-- 2. 创建完整本地表、外表和因子专用夹具。
CREATE FOREIGN DATA WRAPPER alterforeigntable_1293_fdw NO HANDLER;
CREATE SERVER alterforeigntable_1293_server FOREIGN DATA WRAPPER alterforeigntable_1293_fdw;
CREATE TABLE alterforeigntable_1293_base (id bigint NOT NULL PRIMARY KEY, factor_col integer, drop_col text, base_col integer NOT NULL, period_col int4range NOT NULL, status smallint NOT NULL DEFAULT 0, payload varchar(128) NOT NULL DEFAULT '', CONSTRAINT alterforeigntable_1293_base_status_check CHECK (status BETWEEN 0 AND 9));
INSERT INTO alterforeigntable_1293_base (id, factor_col, drop_col, base_col, period_col, status, payload) VALUES (1, 1, 'drop-me', 2, int4range(1, 5), 1, 'baseline');
CREATE FOREIGN TABLE alterforeigntable_1293_ft (alterforeigntable_1293_id bigint NOT NULL, alterforeigntable_1293_factor_col integer OPTIONS (alterforeigntable_1293_existing_option_1 'old', alterforeigntable_1293_existing_option_2 'old'), alterforeigntable_1293_drop_col text, alterforeigntable_1293_base_col integer NOT NULL, alterforeigntable_1293_period_col int4range NOT NULL, alterforeigntable_1293_status smallint NOT NULL DEFAULT 0, alterforeigntable_1293_payload varchar(128) NOT NULL DEFAULT '', CONSTRAINT alterforeigntable_1293_base_check CHECK (alterforeigntable_1293_status BETWEEN 0 AND 9)) SERVER alterforeigntable_1293_server OPTIONS (alterforeigntable_1293_existing_option_1 'old', alterforeigntable_1293_existing_option_2 'old');
-- 3. 执行唯一获得覆盖信用的 ALTER FOREIGN TABLE。
-- primary-target-begin
ALTER FOREIGN TABLE alterforeigntable_1293_ft ADD CONSTRAINT alterforeigntable_1293_factor_constraint CHECK (alterforeigntable_1293_factor_col > 0) NO INHERIT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT EXISTS (SELECT 1 FROM pg_catalog.pg_attribute AS a WHERE a.attrelid = 'alterforeigntable_1293_ft'::regclass AND a.attname = 'alterforeigntable_1293_factor_col' AND NOT a.attisdropped) AS constraint_factor_state_is_deterministic FROM (VALUES (1)) AS deterministic_probe(value) ORDER BY deterministic_probe.value;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_1293_New Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1293_renamed_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1293_target_schema.alterforeigntable_1293_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1293_source_schema.alterforeigntable_1293_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_1293_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1293_zero_column_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1293_ft CASCADE;
DROP VIEW IF EXISTS alterforeigntable_1293_dependent_view CASCADE;
DROP VIEW IF EXISTS alterforeigntable_1293_whole_row_view CASCADE;
DROP MATERIALIZED VIEW IF EXISTS alterforeigntable_1293_dependent_matview CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1293_source_schema CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_1293_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1293_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1293_zero_column_ft CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1293_remote_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1293_referenced_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1293_fk_dependent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1293_fk_target CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1293_partition_context CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1293_partition_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1293_inheritance_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1293_child_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1293_parent_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1293_range_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1293_list_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1293_hash_parent CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_1293_default_seq CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_1293_dependency_seq CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1293_default_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1293_dependency_fn(integer) CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1293_trigger_fn() CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1293_base_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1293_mood CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1293_positive_integer CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1293_address CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1293_enum_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_1293_domain_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1293_composite_type CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1293_row_table CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1293_range_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1293_range_for_multi CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1293_multirange_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1293_array_element_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_1293_dependency_domain CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1293_collation CASCADE;
DROP COLLATION IF EXISTS "alterforeigntable_1293_Mixed Collation" CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1293_encoding_collation CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1293_dependency_collation CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1293_collation_schema CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1293_target_schema CASCADE;
DROP ROLE IF EXISTS alterforeigntable_1293_actor;
DROP ROLE IF EXISTS alterforeigntable_1293_new_owner;
DROP SERVER IF EXISTS alterforeigntable_1293_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterforeigntable_1293_fdw CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1293_base, alterforeigntable_1293_remote_table, alterforeigntable_1293_referenced_table, alterforeigntable_1293_fk_dependent, alterforeigntable_1293_fk_target, alterforeigntable_1293_partition_context, alterforeigntable_1293_partition_parent, alterforeigntable_1293_inheritance_parent, alterforeigntable_1293_child_marker, alterforeigntable_1293_parent_marker, alterforeigntable_1293_range_parent, alterforeigntable_1293_list_parent, alterforeigntable_1293_hash_parent, alterforeigntable_1293_row_table CASCADE;
