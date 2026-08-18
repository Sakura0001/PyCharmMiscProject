-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-18
-- version      : 1.0
-- description  : ALTER FOREIGN TABLE local:column_keyword=omitted
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERFOREIGNTABLE0070
-- source_md: skills/pg-sql-generation/references/statements/ddl/foreign_table/alter_foreign_table.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/foreign_table/alter_foreign_table.yaml
-- primary_obligation_id: AFT-GRM|branch_action_list|set_not_null|column_keyword|omitted
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterforeigntable_0070_base, alterforeigntable_0070_remote_table, alterforeigntable_0070_referenced_table, alterforeigntable_0070_fk_dependent, alterforeigntable_0070_fk_target, alterforeigntable_0070_partition_context, alterforeigntable_0070_partition_parent, alterforeigntable_0070_inheritance_parent, alterforeigntable_0070_child_marker, alterforeigntable_0070_parent_marker, alterforeigntable_0070_range_parent, alterforeigntable_0070_list_parent, alterforeigntable_0070_hash_parent, alterforeigntable_0070_row_table CASCADE;
\set ON_ERROR_STOP on
RESET ROLE;
DROP VIEW IF EXISTS alterforeigntable_0070_dependent_view CASCADE;
DROP VIEW IF EXISTS alterforeigntable_0070_whole_row_view CASCADE;
DROP MATERIALIZED VIEW IF EXISTS alterforeigntable_0070_dependent_matview CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_0070_source_schema CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_0070_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0070_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0070_zero_column_ft CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0070_remote_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0070_referenced_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0070_fk_dependent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0070_fk_target CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0070_partition_context CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0070_partition_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0070_inheritance_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0070_child_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0070_parent_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0070_range_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0070_list_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0070_hash_parent CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_0070_default_seq CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_0070_dependency_seq CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0070_default_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0070_dependency_fn(integer) CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0070_trigger_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0070_base_in(cstring) CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0070_base_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0070_mood CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0070_positive_integer CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0070_address CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0070_enum_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_0070_domain_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0070_composite_type CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0070_row_table CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0070_range_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0070_range_for_multi CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0070_multirange_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0070_array_element_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_0070_dependency_domain CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_0070_collation CASCADE;
DROP COLLATION IF EXISTS "alterforeigntable_0070_Mixed Collation" CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_0070_encoding_collation CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_0070_dependency_collation CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_0070_collation_schema CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_0070_target_schema CASCADE;
DROP ROLE IF EXISTS alterforeigntable_0070_actor;
DROP ROLE IF EXISTS alterforeigntable_0070_new_owner;
DROP SERVER IF EXISTS alterforeigntable_0070_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterforeigntable_0070_fdw CASCADE;
-- 2. 创建完整本地表、外表和因子专用夹具。
CREATE FOREIGN DATA WRAPPER alterforeigntable_0070_fdw NO HANDLER;
CREATE SERVER alterforeigntable_0070_server FOREIGN DATA WRAPPER alterforeigntable_0070_fdw;
CREATE TABLE alterforeigntable_0070_base (id bigint NOT NULL PRIMARY KEY, factor_col integer, drop_col text, base_col integer NOT NULL, period_col int4range NOT NULL, status smallint NOT NULL DEFAULT 0, payload varchar(128) NOT NULL DEFAULT '', CONSTRAINT alterforeigntable_0070_base_status_check CHECK (status BETWEEN 0 AND 9));
INSERT INTO alterforeigntable_0070_base (id, factor_col, drop_col, base_col, period_col, status, payload) VALUES (1, 1, 'drop-me', 2, int4range(1, 5), 1, 'baseline');
CREATE FOREIGN TABLE alterforeigntable_0070_ft (alterforeigntable_0070_id bigint NOT NULL, alterforeigntable_0070_factor_col integer OPTIONS (alterforeigntable_0070_existing_option_1 'old', alterforeigntable_0070_existing_option_2 'old'), alterforeigntable_0070_drop_col text, alterforeigntable_0070_base_col integer NOT NULL, alterforeigntable_0070_period_col int4range NOT NULL, alterforeigntable_0070_status smallint NOT NULL DEFAULT 0, alterforeigntable_0070_payload varchar(128) NOT NULL DEFAULT '', CONSTRAINT alterforeigntable_0070_base_check CHECK (alterforeigntable_0070_status BETWEEN 0 AND 9)) SERVER alterforeigntable_0070_server OPTIONS (alterforeigntable_0070_existing_option_1 'old', alterforeigntable_0070_existing_option_2 'old');
-- 3. 执行唯一获得覆盖信用的 ALTER FOREIGN TABLE。
-- primary-target-begin
ALTER FOREIGN TABLE alterforeigntable_0070_ft ALTER alterforeigntable_0070_factor_col SET NOT NULL;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT 'local:column_keyword'::text AS grammar_axis, 'omitted'::text AS grammar_value;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_0070_New Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0070_renamed_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0070_target_schema.alterforeigntable_0070_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0070_source_schema.alterforeigntable_0070_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_0070_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0070_zero_column_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0070_ft CASCADE;
DROP VIEW IF EXISTS alterforeigntable_0070_dependent_view CASCADE;
DROP VIEW IF EXISTS alterforeigntable_0070_whole_row_view CASCADE;
DROP MATERIALIZED VIEW IF EXISTS alterforeigntable_0070_dependent_matview CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_0070_source_schema CASCADE;
DROP FOREIGN TABLE IF EXISTS "alterforeigntable_0070_Mixed Foreign Table" CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0070_ft CASCADE;
DROP FOREIGN TABLE IF EXISTS alterforeigntable_0070_zero_column_ft CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0070_remote_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0070_referenced_table CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0070_fk_dependent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0070_fk_target CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0070_partition_context CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0070_partition_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0070_inheritance_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0070_child_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0070_parent_marker CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0070_range_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0070_list_parent CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0070_hash_parent CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_0070_default_seq CASCADE;
DROP SEQUENCE IF EXISTS alterforeigntable_0070_dependency_seq CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0070_default_fn() CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0070_dependency_fn(integer) CASCADE;
DROP FUNCTION IF EXISTS alterforeigntable_0070_trigger_fn() CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0070_base_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0070_mood CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0070_positive_integer CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0070_address CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0070_enum_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_0070_domain_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0070_composite_type CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0070_row_table CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0070_range_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0070_range_for_multi CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0070_multirange_type CASCADE;
DROP TYPE IF EXISTS alterforeigntable_0070_array_element_type CASCADE;
DROP DOMAIN IF EXISTS alterforeigntable_0070_dependency_domain CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_0070_collation CASCADE;
DROP COLLATION IF EXISTS "alterforeigntable_0070_Mixed Collation" CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_0070_encoding_collation CASCADE;
DROP COLLATION IF EXISTS alterforeigntable_0070_dependency_collation CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_0070_collation_schema CASCADE;
DROP SCHEMA IF EXISTS alterforeigntable_0070_target_schema CASCADE;
DROP ROLE IF EXISTS alterforeigntable_0070_actor;
DROP ROLE IF EXISTS alterforeigntable_0070_new_owner;
DROP SERVER IF EXISTS alterforeigntable_0070_server CASCADE;
DROP FOREIGN DATA WRAPPER IF EXISTS alterforeigntable_0070_fdw CASCADE;
DROP TABLE IF EXISTS alterforeigntable_0070_base, alterforeigntable_0070_remote_table, alterforeigntable_0070_referenced_table, alterforeigntable_0070_fk_dependent, alterforeigntable_0070_fk_target, alterforeigntable_0070_partition_context, alterforeigntable_0070_partition_parent, alterforeigntable_0070_inheritance_parent, alterforeigntable_0070_child_marker, alterforeigntable_0070_parent_marker, alterforeigntable_0070_range_parent, alterforeigntable_0070_list_parent, alterforeigntable_0070_hash_parent, alterforeigntable_0070_row_table CASCADE;
