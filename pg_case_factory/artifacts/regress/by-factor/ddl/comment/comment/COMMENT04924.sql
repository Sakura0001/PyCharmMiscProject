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
-- case_id: COMMENT04924
-- source_md: skills/pg-sql-generation/references/statements/ddl/comment/comment.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/comment/comment.yaml
-- primary_obligation_id: COMMENT-EXT|04924|shobj_description_query|drop_prerequisite_object
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP OPERATOR CLASS IF EXISTS comment_04924_opc USING btree;
DROP OPERATOR FAMILY IF EXISTS comment_04924_opf USING btree;
DROP OWNED BY comment_04924_actor CASCADE;
DROP ROLE IF EXISTS comment_04924_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE comment_04924_actor LOGIN NOSUPERUSER;
CREATE OPERATOR FAMILY comment_04924_opf USING btree;
CREATE OPERATOR CLASS comment_04924_opc FOR TYPE int USING btree FAMILY comment_04924_opf AS STORAGE int;
SET ROLE comment_04924_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 COMMENT ON。
-- primary-target-begin
COMMENT ON OPERATOR CLASS comment_04924_opc USING btree IS NULL;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT shobj_description('comment_04924_role'::regrole, 'pg_authid') AS comment ORDER BY comment;
-- 5. 清理全部本编号对象。
DROP OWNED BY comment_04924_actor CASCADE;
DROP ROLE IF EXISTS comment_04924_actor;
DROP OPERATOR CLASS IF EXISTS comment_04924_opc USING btree;
DROP OPERATOR FAMILY IF EXISTS comment_04924_opf USING btree;
