-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : UPDATE result_shape=rowset_projection
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: UPDATE00039
-- source_md: skills/pg-sql-generation/references/statements/dml/table/update.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/table/update.yaml
-- primary_obligation_id: UPDATE-SFV|sfv-105029eaaf39bb4f5fb40490|update
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS update_00039_tbl, update_00039_src, update_00039_ref CASCADE;
RESET ROLE;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE update_00039_tbl (id int, val int);
INSERT INTO update_00039_tbl VALUES (1, 100), (2, 200);
-- 3. 执行唯一获得覆盖信用的 UPDATE。
-- primary-target-begin
UPDATE update_00039_tbl SET val = 1 WHERE id = 1 RETURNING id, val;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) >= 0 AS effect_state FROM update_00039_tbl ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS update_00039_tbl, update_00039_src, update_00039_ref CASCADE;
