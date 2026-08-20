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
-- case_id: COMMENT09542
-- source_md: skills/pg-sql-generation/references/statements/ddl/comment/comment.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/comment/comment.yaml
-- primary_obligation_id: COMMENT-EXT|09542|col_description_query|comment_is_null_cleanup
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP FUNCTION IF EXISTS comment_09542_fn();
DROP OWNED BY comment_09542_actor CASCADE;
DROP ROLE IF EXISTS comment_09542_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE comment_09542_actor LOGIN NOSUPERUSER;
CREATE FUNCTION comment_09542_fn() RETURNS int AS $$SELECT 1;$$ LANGUAGE sql;
SET ROLE comment_09542_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 COMMENT ON。
-- primary-target-begin
COMMENT ON ROUTINE comment_09542_fn() IS 'short comment';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT col_description('comment_09542_tbl'::regclass, 1) AS comment ORDER BY comment;
-- 5. 清理全部本编号对象。
DROP OWNED BY comment_09542_actor CASCADE;
DROP ROLE IF EXISTS comment_09542_actor;
DROP FUNCTION IF EXISTS comment_09542_fn();
