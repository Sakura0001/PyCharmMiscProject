-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : COMMENT ON object_type=event_trigger
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: COMMENT12209
-- source_md: skills/pg-sql-generation/references/statements/ddl/comment/comment.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/comment/comment.yaml
-- primary_obligation_id: COMMENT-EXT|12209|obj_description_query|comment_is_null_cleanup
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP EVENT TRIGGER IF EXISTS comment_12209_et;
DROP FUNCTION IF EXISTS comment_12209_etfn();
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE FUNCTION comment_12209_etfn() RETURNS event_trigger AS $$BEGIN NULL; END;$$ LANGUAGE plpgsql;
CREATE EVENT TRIGGER comment_12209_et ON ddl_command_start EXECUTE FUNCTION comment_12209_etfn();
-- 3. 执行唯一获得覆盖信用的 COMMENT ON。
-- primary-target-begin
COMMENT ON EVENT TRIGGER comment_12209_et IS 'short comment';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT obj_description('comment_12209_tbl'::regclass) AS comment ORDER BY comment;
-- 5. 清理全部本编号对象。
DROP EVENT TRIGGER IF EXISTS comment_12209_et;
DROP FUNCTION IF EXISTS comment_12209_etfn();
