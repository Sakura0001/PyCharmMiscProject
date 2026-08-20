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
-- case_id: COMMENT09148
-- source_md: skills/pg-sql-generation/references/statements/ddl/comment/comment.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/comment/comment.yaml
-- primary_obligation_id: COMMENT-EXT|09148|obj_description_query|drop_prerequisite_object
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP ACCESS METHOD IF EXISTS comment_09148_am;
DROP FUNCTION IF EXISTS comment_09148_amhandler(internal);
DROP OWNED BY comment_09148_actor CASCADE;
DROP ROLE IF EXISTS comment_09148_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE comment_09148_actor LOGIN NOSUPERUSER;
CREATE FUNCTION comment_09148_amhandler(internal) RETURNS table_am_handler AS 'no_op' LANGUAGE internal;
CREATE ACCESS METHOD comment_09148_am TYPE TABLE HANDLER comment_09148_amhandler;
SET ROLE comment_09148_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 COMMENT ON。
-- primary-target-begin
COMMENT ON ACCESS METHOD comment_09148_am IS 'short comment';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT obj_description('comment_09148_tbl'::regclass) AS comment ORDER BY comment;
-- 5. 清理全部本编号对象。
DROP OWNED BY comment_09148_actor CASCADE;
DROP ROLE IF EXISTS comment_09148_actor;
DROP ACCESS METHOD IF EXISTS comment_09148_am;
DROP FUNCTION IF EXISTS comment_09148_amhandler(internal);
