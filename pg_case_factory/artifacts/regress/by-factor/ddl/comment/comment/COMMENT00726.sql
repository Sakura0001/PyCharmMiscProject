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
-- case_id: COMMENT00726
-- source_md: skills/pg-sql-generation/references/statements/ddl/comment/comment.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/comment/comment.yaml
-- primary_obligation_id: COMMENT-EXT|00726|shobj_description_query|cascade_drop
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS comment_00726_tbl CASCADE;
DROP FUNCTION IF EXISTS comment_00726_trigfn();
DROP OWNED BY comment_00726_actor CASCADE;
DROP ROLE IF EXISTS comment_00726_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE comment_00726_actor LOGIN NOSUPERUSER;
CREATE TABLE comment_00726_tbl (id int);
CREATE FUNCTION comment_00726_trigfn() RETURNS trigger AS $$BEGIN RETURN NULL; END;$$ LANGUAGE plpgsql;
CREATE TRIGGER comment_00726_trig BEFORE INSERT ON comment_00726_tbl FOR EACH ROW EXECUTE FUNCTION comment_00726_trigfn();
SET ROLE comment_00726_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 COMMENT ON。
-- primary-target-begin
COMMENT ON TRIGGER comment_00726_trig ON comment_00726_tbl IS '';
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT shobj_description('comment_00726_role'::regrole, 'pg_authid') AS comment ORDER BY comment;
-- 5. 清理全部本编号对象。
DROP OWNED BY comment_00726_actor CASCADE;
DROP ROLE IF EXISTS comment_00726_actor;
DROP FUNCTION IF EXISTS comment_00726_trigfn();
DROP TABLE IF EXISTS comment_00726_tbl;
