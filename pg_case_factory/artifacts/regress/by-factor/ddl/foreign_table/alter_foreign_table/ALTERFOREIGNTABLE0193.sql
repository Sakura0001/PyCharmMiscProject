-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-18
-- version      : 1.0
-- description  : ALTER FOREIGN TABLE non_owner_attempt=non_owner_execution
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERFOREIGNTABLE0193
-- source_md: skills/pg-sql-generation/references/statements/ddl/foreign_table/alter_foreign_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/foreign_table/alter_foreign_table.yaml
-- primary_obligation_id: AFT-SFV|sfv-41f49dc0363a439e0ddb0334|add_column
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterforeigntable_0193_base, alterforeigntable_0193_remote_table, alterforeigntable_0193_referenced_table, alterforeigntable_0193_fk_dependent, alterforeigntable_0193_fk_target, alterforeigntable_0193_partition_context, alterforeigntable_0193_partition_parent, alterforeigntable_0193_inheritance_parent, alterforeigntable_0193_child_marker, alterforeigntable_0193_parent_marker, alterforeigntable_0193_range_parent, alterforeigntable_0193_list_parent, alterforeigntable_0193_hash_parent, alterforeigntable_0193_row_table CASCADE;
\set ON_ERROR_STOP on
RESET ROLE;
DROP VIEW IF EXISTS alterforeigntable_0193_dependent_view CASCADE;
DROP VIEW IF EXISTS alterforeigntable_0193_whole_row_view CASCADE;
DROP MATERIALIZED VIEW IF EXISTS alterforeigntable_0193_dependent_matview CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_0193_source_schema CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_0193_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0193_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0193_zero_column_ft CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0193_remote_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0193_referenced_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0193_fk_dependent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0193_fk_target CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0193_partition_context CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0193_partition_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0193_inheritance_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0193_child_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0193_parent_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0193_range_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0193_list_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0193_hash_parent CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_0193_default_seq CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_0193_dependency_seq CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0193_default_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0193_dependency_fn(integer) CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0193_trigger_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0193_base_in(cstring) CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0193_base_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0193_mood CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0193_positive_integer CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0193_address CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0193_enum_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_0193_domain_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0193_composite_type CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0193_row_table CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0193_range_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0193_range_for_multi CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0193_multirange_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0193_array_element_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_0193_dependency_domain CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_0193_collation CASCADE;
DROP COLLATION IF EXISTS "alterforeigntable_0193_Mixed Collation" CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_0193_encoding_collation CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_0193_dependency_collation CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_0193_collation_schema CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_0193_target_schema CASCADE;
DROP ROLE IF EXISTS alterforeigntable_0193_actor;
DROP ROLE IF EXISTS alterforeigntable_0193_new_owner;
DROP SERVER IF EXISTS alterforeigntable_0193_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterforeigntable_0193_fdw CASCADE;
-- 2. 创建完整本地表、外表和因子专用夹具。
CREATE FOREIGN DATA WRAPPER alterforeigntable_0193_fdw NO HANDLER;
CREATE SERVER alterforeigntable_0193_server FOREIGN DATA WRAPPER alterforeigntable_0193_fdw;
CREATE TABLE alterforeigntable_0193_base (id bigint NOT NULL PRIMARY KEY, factor_col integer, drop_col text, base_col integer NOT NULL, period_col int4range NOT NULL, status smallint NOT NULL DEFAULT 0, payload varchar(128) NOT NULL DEFAULT '', CONSTRAINT alterforeigntable_0193_base_status_check CHECK (status BETWEEN 0 AND 9));
INSERT INTO alterforeigntable_0193_base (id, factor_col, drop_col, base_col, period_col, status, payload) VALUES (1, 1, 'drop-me', 2, int4range(1, 5), 1, 'baseline');
CREATE FOREIGN TABLE alterforeigntable_0193_ft (alterforeigntable_0193_id bigint NOT NULL, alterforeigntable_0193_factor_col integer OPTIONS (alterforeigntable_0193_existing_option_1 'old', alterforeigntable_0193_existing_option_2 'old'), alterforeigntable_0193_drop_col text, alterforeigntable_0193_base_col integer NOT NULL, alterforeigntable_0193_period_col int4range NOT NULL, alterforeigntable_0193_status smallint NOT NULL DEFAULT 0, alterforeigntable_0193_payload varchar(128) NOT NULL DEFAULT '', CONSTRAINT alterforeigntable_0193_base_check CHECK (alterforeigntable_0193_status BETWEEN 0 AND 9)) SERVER alterforeigntable_0193_server OPTIONS (alterforeigntable_0193_existing_option_1 'old', alterforeigntable_0193_existing_option_2 'old');
CREATE ROLE alterforeigntable_0193_actor NOLOGIN;
SET ROLE alterforeigntable_0193_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER FOREIGN TABLE。
-- primary-target-begin
ALTER FOREIGN TABLE alterforeigntable_0193_ft ADD alterforeigntable_0193_grammar_col text;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT 'non_owner_attempt'::text AS canonical_factor, 'non_owner_execution'::text AS canonical_value;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_0193_New Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0193_renamed_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0193_target_schema.alterforeigntable_0193_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0193_source_schema.alterforeigntable_0193_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_0193_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0193_zero_column_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0193_ft CASCADE;
DROP VIEW IF EXISTS alterforeigntable_0193_dependent_view CASCADE;
DROP VIEW IF EXISTS alterforeigntable_0193_whole_row_view CASCADE;
DROP MATERIALIZED VIEW IF EXISTS alterforeigntable_0193_dependent_matview CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_0193_source_schema CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_0193_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0193_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0193_zero_column_ft CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0193_remote_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0193_referenced_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0193_fk_dependent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0193_fk_target CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0193_partition_context CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0193_partition_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0193_inheritance_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0193_child_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0193_parent_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0193_range_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0193_list_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0193_hash_parent CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_0193_default_seq CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_0193_dependency_seq CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0193_default_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0193_dependency_fn(integer) CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0193_trigger_fn() CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0193_base_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0193_mood CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0193_positive_integer CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0193_address CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0193_enum_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_0193_domain_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0193_composite_type CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0193_row_table CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0193_range_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0193_range_for_multi CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0193_multirange_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0193_array_element_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_0193_dependency_domain CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_0193_collation CASCADE;
DROP COLLATION IF EXISTS "alterforeigntable_0193_Mixed Collation" CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_0193_encoding_collation CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_0193_dependency_collation CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_0193_collation_schema CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_0193_target_schema CASCADE;
DROP ROLE IF EXISTS alterforeigntable_0193_actor;
DROP ROLE IF EXISTS alterforeigntable_0193_new_owner;
DROP SERVER IF EXISTS alterforeigntable_0193_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterforeigntable_0193_fdw CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0193_base, alterforeigntable_0193_remote_table, alterforeigntable_0193_referenced_table, alterforeigntable_0193_fk_dependent, alterforeigntable_0193_fk_target, alterforeigntable_0193_partition_context, alterforeigntable_0193_partition_parent, alterforeigntable_0193_inheritance_parent, alterforeigntable_0193_child_marker, alterforeigntable_0193_parent_marker, alterforeigntable_0193_range_parent, alterforeigntable_0193_list_parent, alterforeigntable_0193_hash_parent, alterforeigntable_0193_row_table CASCADE;
