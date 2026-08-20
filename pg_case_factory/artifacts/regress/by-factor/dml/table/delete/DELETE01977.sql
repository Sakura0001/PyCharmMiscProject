-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DELETE target_relation_state=wrong_object_type
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DELETE01977
-- source_md: skills/pg-sql-generation/references/statements/dml/table/delete.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/table/delete.yaml
-- primary_obligation_id: DELETE-EXT|01977|returned_rows|rollback
-- expected_outcome: expected_failure
-- expected_sqlstate: 42809
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS delete_01977_tbl, delete_01977_src, delete_01977_ref CASCADE;
DROP SEQUENCE IF EXISTS delete_01977_seq;
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SEQUENCE delete_01977_seq;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DELETE。
-- primary-target-begin
DELETE FROM delete_01977_seq AS d WHERE id = abs(1);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42809' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS effect_state FROM pg_catalog.pg_class WHERE relname = 'delete_01977_seq' AND relkind = 'r' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP SEQUENCE IF EXISTS delete_01977_seq;
DROP TABLE IF EXISTS delete_01977_tbl, delete_01977_src, delete_01977_ref CASCADE;
