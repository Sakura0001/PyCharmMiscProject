-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-18
-- version      : 1.0
-- description  : ALTER FOREIGN TABLE inheritance_role=partition_inherited_column
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERFOREIGNTABLE1501
-- source_md: skills/pg-sql-generation/references/statements/ddl/foreign_table/alter_foreign_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/foreign_table/alter_foreign_table.yaml
-- primary_obligation_id: AFT-INV|drop_column|inheritance_role|partition_inherited_column
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterforeigntable_1501_base, alterforeigntable_1501_remote_table, alterforeigntable_1501_referenced_table, alterforeigntable_1501_fk_dependent, alterforeigntable_1501_fk_target, alterforeigntable_1501_partition_context, alterforeigntable_1501_partition_parent, alterforeigntable_1501_inheritance_parent, alterforeigntable_1501_child_marker, alterforeigntable_1501_parent_marker, alterforeigntable_1501_range_parent, alterforeigntable_1501_list_parent, alterforeigntable_1501_hash_parent, alterforeigntable_1501_row_table CASCADE;
\set ON_ERROR_STOP on
RESET ROLE;
DROP VIEW IF EXISTS alterforeigntable_1501_dependent_view CASCADE;
DROP VIEW IF EXISTS alterforeigntable_1501_whole_row_view CASCADE;
DROP MATERIALIZED VIEW IF EXISTS alterforeigntable_1501_dependent_matview CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1501_source_schema CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_1501_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1501_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1501_zero_column_ft CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1501_remote_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1501_referenced_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1501_fk_dependent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1501_fk_target CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1501_partition_context CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1501_partition_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1501_inheritance_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1501_child_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1501_parent_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1501_range_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1501_list_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1501_hash_parent CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_1501_default_seq CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_1501_dependency_seq CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1501_default_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1501_dependency_fn(integer) CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1501_trigger_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1501_base_in(cstring) CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1501_base_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1501_mood CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1501_positive_integer CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1501_address CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1501_enum_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_1501_domain_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1501_composite_type CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1501_row_table CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1501_range_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1501_range_for_multi CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1501_multirange_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1501_array_element_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_1501_dependency_domain CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1501_collation CASCADE;
DROP COLLATION IF EXISTS "alterforeigntable_1501_Mixed Collation" CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1501_encoding_collation CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1501_dependency_collation CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1501_collation_schema CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1501_target_schema CASCADE;
DROP ROLE IF EXISTS alterforeigntable_1501_actor;
DROP ROLE IF EXISTS alterforeigntable_1501_new_owner;
DROP SERVER IF EXISTS alterforeigntable_1501_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterforeigntable_1501_fdw CASCADE;
-- 2. 创建完整本地表、外表和因子专用夹具。
CREATE FOREIGN DATA WRAPPER alterforeigntable_1501_fdw NO HANDLER;
CREATE SERVER alterforeigntable_1501_server FOREIGN DATA WRAPPER alterforeigntable_1501_fdw;
CREATE TABLE alterforeigntable_1501_base (id bigint NOT NULL PRIMARY KEY, factor_col integer, drop_col text, base_col integer NOT NULL, period_col int4range NOT NULL, status smallint NOT NULL DEFAULT 0, payload varchar(128) NOT NULL DEFAULT '', CONSTRAINT alterforeigntable_1501_base_status_check CHECK (status BETWEEN 0 AND 9));
INSERT INTO alterforeigntable_1501_base (id, factor_col, drop_col, base_col, period_col, status, payload) VALUES (1, 1, 'drop-me', 2, int4range(1, 5), 1, 'baseline');
CREATE FOREIGN TABLE alterforeigntable_1501_ft (alterforeigntable_1501_id bigint NOT NULL, alterforeigntable_1501_factor_col integer OPTIONS (alterforeigntable_1501_existing_option_1 'old', alterforeigntable_1501_existing_option_2 'old'), alterforeigntable_1501_drop_col text, alterforeigntable_1501_base_col integer NOT NULL, alterforeigntable_1501_period_col int4range NOT NULL, alterforeigntable_1501_status smallint NOT NULL DEFAULT 0, alterforeigntable_1501_payload varchar(128) NOT NULL DEFAULT '', CONSTRAINT alterforeigntable_1501_base_check CHECK (alterforeigntable_1501_status BETWEEN 0 AND 9)) SERVER alterforeigntable_1501_server OPTIONS (alterforeigntable_1501_existing_option_1 'old', alterforeigntable_1501_existing_option_2 'old');
-- 3. 执行唯一获得覆盖信用的 ALTER FOREIGN TABLE。
-- primary-target-begin
ALTER FOREIGN TABLE alterforeigntable_1501_ft DROP COLUMN alterforeigntable_1501_factor_col;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT 'partition_inherited_column'::text AS topology_role, true AS topology_role_normalized;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_1501_New Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1501_renamed_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1501_target_schema.alterforeigntable_1501_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1501_source_schema.alterforeigntable_1501_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_1501_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1501_zero_column_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1501_ft CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1501_partition_context CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1501_inheritance_parent CASCADE;
DROP VIEW IF EXISTS alterforeigntable_1501_dependent_view CASCADE;
DROP VIEW IF EXISTS alterforeigntable_1501_whole_row_view CASCADE;
DROP MATERIALIZED VIEW IF EXISTS alterforeigntable_1501_dependent_matview CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1501_source_schema CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_1501_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1501_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_1501_zero_column_ft CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1501_remote_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1501_referenced_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1501_fk_dependent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1501_fk_target CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1501_partition_context CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1501_partition_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1501_inheritance_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1501_child_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1501_parent_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1501_range_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1501_list_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1501_hash_parent CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_1501_default_seq CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_1501_dependency_seq CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1501_default_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1501_dependency_fn(integer) CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_1501_trigger_fn() CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1501_base_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1501_mood CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1501_positive_integer CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1501_address CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1501_enum_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_1501_domain_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1501_composite_type CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1501_row_table CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1501_range_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1501_range_for_multi CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1501_multirange_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_1501_array_element_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_1501_dependency_domain CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1501_collation CASCADE;
DROP COLLATION IF EXISTS "alterforeigntable_1501_Mixed Collation" CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1501_encoding_collation CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_1501_dependency_collation CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1501_collation_schema CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_1501_target_schema CASCADE;
DROP ROLE IF EXISTS alterforeigntable_1501_actor;
DROP ROLE IF EXISTS alterforeigntable_1501_new_owner;
DROP SERVER IF EXISTS alterforeigntable_1501_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterforeigntable_1501_fdw CASCADE;
DROP TABLE IF EXISTS alterforeigntable_1501_base, alterforeigntable_1501_remote_table, alterforeigntable_1501_referenced_table, alterforeigntable_1501_fk_dependent, alterforeigntable_1501_fk_target, alterforeigntable_1501_partition_context, alterforeigntable_1501_partition_parent, alterforeigntable_1501_inheritance_parent, alterforeigntable_1501_child_marker, alterforeigntable_1501_parent_marker, alterforeigntable_1501_range_parent, alterforeigntable_1501_list_parent, alterforeigntable_1501_hash_parent, alterforeigntable_1501_row_table CASCADE;
