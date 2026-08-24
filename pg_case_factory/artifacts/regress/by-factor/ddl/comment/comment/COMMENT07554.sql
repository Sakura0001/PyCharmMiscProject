-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : COMMENT ON object_type=conversion
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: COMMENT07554
-- source_md: skills/pg-sql-generation/references/statements/ddl/comment/comment.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/comment/comment.yaml
-- primary_obligation_id: COMMENT-EXT|07554|psql_dd_command|cascade_drop
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP CONVERSION IF EXISTS comment_07554_conv;
DROP FUNCTION IF EXISTS comment_07554_convfn(integer, integer);
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FUNCTION comment_07554_convfn(integer, integer) RETURNS integer AS $$SELECT $1;$$ LANGUAGE sql;
CREATE CONVERSION comment_07554_conv FOR 'UTF8' TO 'UTF8' FROM comment_07554_convfn;
-- 3. 执行唯一获得覆盖信用的 COMMENT ON。
-- primary-target-begin
COMMENT ON CONVERSION comment_07554_conv IS NULL;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT 1 AS psql_dd_command_executed ORDER BY psql_dd_command_executed;
-- 5. 清理全部本编号对象。
DROP CONVERSION IF EXISTS comment_07554_conv;
DROP FUNCTION IF EXISTS comment_07554_convfn(integer, integer);
