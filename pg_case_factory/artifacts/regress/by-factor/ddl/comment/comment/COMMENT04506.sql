-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : COMMENT ON object_type=trigger
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: COMMENT04506
-- source_md: skills/pg-sql-generation/references/statements/ddl/comment/comment.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/comment/comment.yaml
-- primary_obligation_id: COMMENT-EXT|04506|shobj_description_query|cascade_drop
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS comment_04506_tbl CASCADE;
DROP FUNCTION IF EXISTS comment_04506_trigfn();
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE TABLE comment_04506_tbl (id int);
CREATE FUNCTION comment_04506_trigfn() RETURNS trigger AS $$BEGIN RETURN NULL; END;$$ LANGUAGE plpgsql;
CREATE TRIGGER comment_04506_trig BEFORE INSERT ON comment_04506_tbl FOR EACH ROW EXECUTE FUNCTION comment_04506_trigfn();
-- 3. 执行唯一获得覆盖信用的 COMMENT ON。
-- primary-target-begin
COMMENT ON TRIGGER comment_04506_trig ON comment_04506_tbl IS '';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT shobj_description('comment_04506_role'::regrole, 'pg_authid') AS comment ORDER BY comment;
-- 5. 清理全部本编号对象。
DROP FUNCTION IF EXISTS comment_04506_trigfn();
DROP TABLE IF EXISTS comment_04506_tbl;
