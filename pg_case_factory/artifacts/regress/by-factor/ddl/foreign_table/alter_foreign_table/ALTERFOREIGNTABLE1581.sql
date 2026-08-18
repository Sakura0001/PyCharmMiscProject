-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-18
-- version      : 1.0
-- description  : ALTER FOREIGN TABLE dependency_state=dependent_materialized_view
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERFOREIGNTABLE1581
-- source_md: skills/pg-sql-generation/references/statements/ddl/foreign_table/alter_foreign_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/foreign_table/alter_foreign_table.yaml
-- primary_obligation_id: AFT-INV|drop_column|dependency_state|dependent_materialized_view
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterforeigntable_1581_base, alterforeigntable_1581_remote_table, alterforeigntable_1581_referenced_table, alterforeigntable_1581_fk_dependent, alterforeigntable_1581_fk_target, alterforeigntable_1581_partition_context, alterforeigntable_1581_partition_parent, alterforeigntable_1581_inheritance_parent, alterforeigntable_1581_child_marker, alterforeigntable_1581_parent_marker, alterforeigntable_1581_range_parent, alterforeigntable_1581_list_parent, alterforeigntable_1581_hash_parent, alterforeigntable_1581_row_table CASCADE;
\set ON_ERROR_STOP on
RESET ROLE;
DROP VIEW IF EXISTS alterforeigntable_1581_dependent_view CASCADE;
DROP VIEW IF EXISTS alterforeigntable_1581_whole_row_view CASCADE;
DROP MATERIALIZED VIEW IF EXISTS alterforeigntable_1581_dependent_matview CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1581_source_schema CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_1581_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1581_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1581_zero_column_ft CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1581_remote_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1581_referenced_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1581_fk_dependent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1581_fk_target CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1581_partition_context CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1581_partition_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1581_inheritance_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1581_child_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1581_parent_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1581_range_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1581_list_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1581_hash_parent CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_1581_default_seq CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_1581_dependency_seq CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1581_default_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1581_dependency_fn(integer) CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1581_trigger_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1581_base_in(cstring) CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1581_base_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1581_mood CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1581_positive_integer CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1581_address CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1581_enum_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_1581_domain_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1581_composite_type CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1581_row_table CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1581_range_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1581_range_for_multi CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1581_multirange_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1581_array_element_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_1581_dependency_domain CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1581_collation CASCADE;
DROP COLLATION IF EXISTS "alterforeigntable_1581_Mixed Collation" CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1581_encoding_collation CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1581_dependency_collation CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1581_collation_schema CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1581_target_schema CASCADE;
DROP ROLE IF EXISTS alterforeigntable_1581_actor;
DROP ROLE IF EXISTS alterforeigntable_1581_new_owner;
DROP SERVER IF EXISTS alterforeigntable_1581_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterforeigntable_1581_fdw CASCADE;
-- 2. 创建完整本地表、外表和因子专用夹具。
CREATE FOREIGN DATA WRAPPER alterforeigntable_1581_fdw NO HANDLER;
CREATE SERVER alterforeigntable_1581_server FOREIGN DATA WRAPPER alterforeigntable_1581_fdw;
CREATE TABLE alterforeigntable_1581_base (id bigint NOT NULL PRIMARY KEY, factor_col integer, drop_col text, base_col integer NOT NULL, period_col int4range NOT NULL, status smallint NOT NULL DEFAULT 0, payload varchar(128) NOT NULL DEFAULT '', CONSTRAINT alterforeigntable_1581_base_status_check CHECK (status BETWEEN 0 AND 9));
INSERT INTO alterforeigntable_1581_base (id, factor_col, drop_col, base_col, period_col, status, payload) VALUES (1, 1, 'drop-me', 2, int4range(1, 5), 1, 'baseline');
CREATE FOREIGN TABLE alterforeigntable_1581_ft (alterforeigntable_1581_id bigint NOT NULL, alterforeigntable_1581_factor_col integer OPTIONS (alterforeigntable_1581_existing_option_1 'old', alterforeigntable_1581_existing_option_2 'old'), alterforeigntable_1581_drop_col text, alterforeigntable_1581_base_col integer NOT NULL, alterforeigntable_1581_period_col int4range NOT NULL, alterforeigntable_1581_status smallint NOT NULL DEFAULT 0, alterforeigntable_1581_payload varchar(128) NOT NULL DEFAULT '', CONSTRAINT alterforeigntable_1581_base_check CHECK (alterforeigntable_1581_status BETWEEN 0 AND 9)) SERVER alterforeigntable_1581_server OPTIONS (alterforeigntable_1581_existing_option_1 'old', alterforeigntable_1581_existing_option_2 'old');
CREATE MATERIALIZED VIEW alterforeigntable_1581_dependent_matview AS SELECT alterforeigntable_1581_factor_col FROM alterforeigntable_1581_ft WITH NO DATA;
-- 3. 执行唯一获得覆盖信用的 ALTER FOREIGN TABLE。
-- primary-target-begin
ALTER FOREIGN TABLE alterforeigntable_1581_ft DROP COLUMN alterforeigntable_1581_factor_col CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT 'dependent_materialized_view'::text AS dependency_kind, true AS dependency_outcome_normalized;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_1581_New Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1581_renamed_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1581_target_schema.alterforeigntable_1581_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1581_source_schema.alterforeigntable_1581_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_1581_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1581_zero_column_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1581_ft CASCADE;
DROP MATERIALIZED VIEW IF EXISTS alterforeigntable_1581_dependent_matview CASCADE;
DROP VIEW IF EXISTS alterforeigntable_1581_dependent_view CASCADE;
DROP VIEW IF EXISTS alterforeigntable_1581_whole_row_view CASCADE;
DROP MATERIALIZED VIEW IF EXISTS alterforeigntable_1581_dependent_matview CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1581_source_schema CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_1581_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1581_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1581_zero_column_ft CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1581_remote_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1581_referenced_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1581_fk_dependent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1581_fk_target CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1581_partition_context CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1581_partition_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1581_inheritance_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1581_child_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1581_parent_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1581_range_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1581_list_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1581_hash_parent CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_1581_default_seq CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_1581_dependency_seq CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1581_default_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1581_dependency_fn(integer) CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1581_trigger_fn() CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1581_base_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1581_mood CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1581_positive_integer CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1581_address CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1581_enum_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_1581_domain_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1581_composite_type CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1581_row_table CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1581_range_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1581_range_for_multi CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1581_multirange_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1581_array_element_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_1581_dependency_domain CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1581_collation CASCADE;
DROP COLLATION IF EXISTS "alterforeigntable_1581_Mixed Collation" CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1581_encoding_collation CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1581_dependency_collation CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1581_collation_schema CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1581_target_schema CASCADE;
DROP ROLE IF EXISTS alterforeigntable_1581_actor;
DROP ROLE IF EXISTS alterforeigntable_1581_new_owner;
DROP SERVER IF EXISTS alterforeigntable_1581_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterforeigntable_1581_fdw CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1581_base, alterforeigntable_1581_remote_table, alterforeigntable_1581_referenced_table, alterforeigntable_1581_fk_dependent, alterforeigntable_1581_fk_target, alterforeigntable_1581_partition_context, alterforeigntable_1581_partition_parent, alterforeigntable_1581_inheritance_parent, alterforeigntable_1581_child_marker, alterforeigntable_1581_parent_marker, alterforeigntable_1581_range_parent, alterforeigntable_1581_list_parent, alterforeigntable_1581_hash_parent, alterforeigntable_1581_row_table CASCADE;
