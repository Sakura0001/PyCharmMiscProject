-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : MERGE privilege_context=insufficient_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: MERGE12913
-- source_md: skills/pg-sql-generation/references/statements/dml/table/merge.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/table/merge.yaml
-- primary_obligation_id: MERGE-EXT|12913|returned_rows|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS merge_12913_tbl, merge_12913_src, merge_12913_ref CASCADE;
RESET ROLE;
DROP OWNED BY merge_12913_actor CASCADE;
DROP ROLE IF EXISTS merge_12913_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE merge_12913_actor LOGIN NOSUPERUSER;
CREATE TABLE merge_12913_tbl (id int, val int);
INSERT INTO merge_12913_tbl VALUES (1, 100);
GRANT SELECT ON merge_12913_tbl TO merge_12913_actor;
SET ROLE merge_12913_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 MERGE。
-- primary-target-begin
WITH merge_12913_cte AS (SELECT 1 AS id, 100 AS val)
MERGE INTO public.merge_12913_tbl USING merge_12913_cte AS s ON public.merge_12913_tbl.id = s.id WHEN MATCHED THEN UPDATE SET val = abs(1) WHEN NOT MATCHED THEN INSERT VALUES (s.id, abs(1));
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) >= 0 AS returned_rows_state FROM merge_12913_tbl ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY merge_12913_actor CASCADE;
DROP ROLE IF EXISTS merge_12913_actor;
DROP TABLE IF EXISTS merge_12913_tbl, merge_12913_src, merge_12913_ref CASCADE;
