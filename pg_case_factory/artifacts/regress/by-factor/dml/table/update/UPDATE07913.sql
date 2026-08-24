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
-- case_id: UPDATE07913
-- source_md: skills/pg-sql-generation/references/statements/dml/table/update.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/table/update.yaml
-- primary_obligation_id: UPDATE-EXT|07913|catalog_query|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42809
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS update_07913_tbl, update_07913_src, update_07913_ref CASCADE;
DROP SEQUENCE IF EXISTS update_07913_seq;
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE SEQUENCE update_07913_seq;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 UPDATE。
-- primary-target-begin
WITH update_07913_cte AS (SELECT 1 AS val)
UPDATE public.update_07913_seq SET val = (SELECT val FROM update_07913_cte) WHERE id = 999;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42809' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS relation_state FROM pg_catalog.pg_class WHERE relname = 'update_07913_seq' AND relkind = 'r' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP SEQUENCE IF EXISTS update_07913_seq;
DROP TABLE IF EXISTS update_07913_tbl, update_07913_src, update_07913_ref CASCADE;
