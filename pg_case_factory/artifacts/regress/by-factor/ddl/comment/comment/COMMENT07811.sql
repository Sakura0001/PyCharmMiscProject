-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : COMMENT ON object_type=foreign_table
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: COMMENT07811
-- source_md: skills/pg-sql-generation/references/statements/ddl/comment/comment.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/comment/comment.yaml
-- primary_obligation_id: COMMENT-EXT|07811|catalog_query_pg_description|comment_is_null_cleanup
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FOREIGN TABLE IF EXISTS comment_07811_ft;
DROP SERVER IF EXISTS comment_07811_srv;
DROP FOREIGN DATA WRAPPER IF EXISTS comment_07811_fdw;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FOREIGN DATA WRAPPER comment_07811_fdw;
CREATE SERVER comment_07811_srv FOREIGN DATA WRAPPER comment_07811_fdw;
CREATE FOREIGN TABLE comment_07811_ft (id int) SERVER comment_07811_srv;
-- 3. 执行唯一获得覆盖信用的 COMMENT ON。
-- primary-target-begin
COMMENT ON FOREIGN TABLE comment_07811_ft IS NULL;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) AS comment_count FROM pg_catalog.pg_description WHERE description = '' ORDER BY count(*)
-- 5. 清理全部本编号对象。
DROP FOREIGN TABLE IF EXISTS comment_07811_ft;
DROP SERVER IF EXISTS comment_07811_srv;
DROP FOREIGN DATA WRAPPER IF EXISTS comment_07811_fdw;
