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
-- case_id: COMMENT00750
-- source_md: skills/pg-sql-generation/references/statements/ddl/comment/comment.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/comment/comment.yaml
-- primary_obligation_id: COMMENT-EXT|00750|obj_description_query|cascade_drop
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS comment_00750_tbl CASCADE;
DROP VIEW IF EXISTS comment_00750_vw;
DROP OWNED BY comment_00750_actor CASCADE;
DROP ROLE IF EXISTS comment_00750_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE comment_00750_actor LOGIN NOSUPERUSER;
CREATE TABLE comment_00750_tbl (id int);
CREATE VIEW comment_00750_vw AS SELECT * FROM comment_00750_tbl;
SET ROLE comment_00750_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 COMMENT ON。
-- primary-target-begin
COMMENT ON VIEW comment_00750_vw IS '';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT obj_description('comment_00750_tbl'::regclass) AS comment ORDER BY comment;
-- 5. 清理全部本编号对象。
DROP OWNED BY comment_00750_actor CASCADE;
DROP ROLE IF EXISTS comment_00750_actor;
DROP VIEW IF EXISTS comment_00750_vw;
DROP TABLE IF EXISTS comment_00750_tbl;
