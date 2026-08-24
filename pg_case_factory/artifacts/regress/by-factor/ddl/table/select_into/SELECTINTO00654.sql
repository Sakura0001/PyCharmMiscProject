-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : SELECT INTO table_type=permanent
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: SELECTINTO00654
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/select_into.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/select_into.yaml
-- primary_obligation_id: SELECTINTO-EXT|00654|information_schema_tables|DROP_TABLE_IF_EXISTS
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS selectinto_00654_src, selectinto_00654_t CASCADE;
\set ON_ERROR_STOP on
SELECT 1 AS setup_boundary;
-- 2. 创建完整本地表和因子专用夹具。
CREATE TABLE selectinto_00654_src (id integer, val text);
INSERT INTO selectinto_00654_src VALUES (1, 'a'), (2, 'b');
SELECT 1 AS pre_target_boundary;
-- 3. 执行唯一获得覆盖信用的 SELECT INTO。
-- primary-target-begin
WITH RECURSIVE cte AS (SELECT 1 AS x UNION ALL SELECT x + 1 FROM cte WHERE x < 5) SELECT DISTINCT * INTO TABLE selectinto_00654_t FROM selectinto_00654_src a JOIN selectinto_00654_src b ON a.id = b.id;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS table_count FROM information_schema.tables WHERE table_name = 'selectinto_00654_t' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP TABLE IF EXISTS selectinto_00654_src, selectinto_00654_t CASCADE;
