-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : UPDATE target_relation_state=wrong_object_type
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: UPDATE09106
-- source_md: skills/pg-sql-generation/references/statements/dml/table/update.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/table/update.yaml
-- primary_obligation_id: UPDATE-EXT|09106|returned_rows|drop_objects
-- expected_outcome: expected_failure
-- expected_sqlstate: 42809
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS update_09106_tbl, update_09106_src, update_09106_ref CASCADE;
DROP SEQUENCE IF EXISTS update_09106_seq;
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SEQUENCE update_09106_seq;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 UPDATE。
-- primary-target-begin
UPDATE public.update_09106_seq SET val = 1 WHERE id = 999;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42809' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS effect_state FROM pg_catalog.pg_class WHERE relname = 'update_09106_seq' AND relkind = 'r' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP SEQUENCE IF EXISTS update_09106_seq;
DROP TABLE IF EXISTS update_09106_tbl, update_09106_src, update_09106_ref CASCADE;
