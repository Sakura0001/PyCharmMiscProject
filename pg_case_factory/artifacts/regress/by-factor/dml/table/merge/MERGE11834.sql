-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : MERGE privilege_context=insufficient_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: MERGE11834
-- source_md: skills/pg-sql-generation/references/statements/dml/table/merge.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/table/merge.yaml
-- primary_obligation_id: MERGE-EXT|11834|error_assertion|rollback
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS merge_11834_tbl, merge_11834_src, merge_11834_ref CASCADE;
RESET ROLE;
DROP OWNED BY merge_11834_actor CASCADE;
DROP ROLE IF EXISTS merge_11834_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE merge_11834_actor LOGIN NOSUPERUSER;
CREATE TABLE merge_11834_tbl (id int, val int);
CREATE TABLE merge_11834_src (id int, val int);
INSERT INTO merge_11834_src VALUES (1, 100);
GRANT SELECT ON merge_11834_tbl TO merge_11834_actor;
SET ROLE merge_11834_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 MERGE。
-- primary-target-begin
MERGE INTO merge_11834_tbl USING merge_11834_src AS s ON merge_11834_tbl.id = s.id WHEN MATCHED THEN UPDATE SET val = (SELECT 1) WHEN NOT MATCHED THEN INSERT VALUES (s.id, (SELECT 1));
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY merge_11834_actor CASCADE;
DROP ROLE IF EXISTS merge_11834_actor;
DROP TABLE IF EXISTS merge_11834_tbl, merge_11834_src, merge_11834_ref CASCADE;
