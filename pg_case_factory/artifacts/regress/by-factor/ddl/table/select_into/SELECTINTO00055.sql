-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : SELECT INTO with_clause=with_recursive
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: SELECTINTO00055
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/select_into.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/select_into.yaml
-- primary_obligation_id: SELECTINTO-SFV|sfv-c79cbb735427584ce049c30d|select_into
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS selectinto_00055_src, selectinto_00055_t CASCADE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地表和因子专用夹具。
CREATE TABLE selectinto_00055_src (id integer, val text);
INSERT INTO selectinto_00055_src VALUES (1, 'a'), (2, 'b');
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 SELECT INTO。
-- primary-target-begin
WITH RECURSIVE cte AS (SELECT 1 AS x UNION ALL SELECT x + 1 FROM cte WHERE x < 5) SELECT * INTO selectinto_00055_t FROM selectinto_00055_src;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS table_count FROM pg_catalog.pg_class c WHERE c.relname = 'selectinto_00055_t' AND c.relkind = 'r' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS selectinto_00055_src, selectinto_00055_t CASCADE;
