-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : COMMENT ON privilege_level=non_owner
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: COMMENT04893
-- source_md: skills/pg-sql-generation/references/statements/ddl/comment/comment.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/comment/comment.yaml
-- primary_obligation_id: COMMENT-EXT|04893|col_description_query|cascade_drop
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS comment_04893_tbl CASCADE;
DROP MATERIALIZED VIEW IF EXISTS comment_04893_mv;
DROP OWNED BY comment_04893_actor CASCADE;
DROP ROLE IF EXISTS comment_04893_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE comment_04893_actor LOGIN NOSUPERUSER;
CREATE TABLE comment_04893_tbl (id int);
CREATE MATERIALIZED VIEW comment_04893_mv AS SELECT * FROM comment_04893_tbl;
SET ROLE comment_04893_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 COMMENT ON。
-- primary-target-begin
COMMENT ON MATERIALIZED VIEW comment_04893_mv IS NULL;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT col_description('comment_04893_tbl'::regclass, 1) AS comment ORDER BY comment;
-- 5. 清理全部本编号对象。
DROP OWNED BY comment_04893_actor CASCADE;
DROP ROLE IF EXISTS comment_04893_actor;
DROP MATERIALIZED VIEW IF EXISTS comment_04893_mv;
DROP TABLE IF EXISTS comment_04893_tbl;
