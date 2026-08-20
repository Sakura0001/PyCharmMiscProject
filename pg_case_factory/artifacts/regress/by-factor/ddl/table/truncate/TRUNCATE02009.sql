-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : TRUNCATE privilege_level=insufficient_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: TRUNCATE02009
-- source_md: skills/pg-sql-generation/references/statements/ddl/table/truncate.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/table/truncate.yaml
-- primary_obligation_id: TRUNCATE-EXT|02009|error_assertion|rollback
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS truncate_02009_tbl, truncate_02009_ref CASCADE;
RESET ROLE;
DROP OWNED BY truncate_02009_actor CASCADE;
DROP ROLE IF EXISTS truncate_02009_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE truncate_02009_actor LOGIN NOSUPERUSER;
GRANT USAGE ON SCHEMA public TO truncate_02009_actor;
CREATE TABLE truncate_02009_tbl (id int, val int);
CREATE TABLE truncate_02009_ref (id int, val int);
INSERT INTO truncate_02009_tbl VALUES (1, 100), (2, 200);
INSERT INTO truncate_02009_ref VALUES (1, 100), (2, 200);
SET ROLE truncate_02009_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 TRUNCATE。
-- primary-target-begin
TRUNCATE TABLE truncate_02009_tbl, truncate_02009_ref CONTINUE IDENTITY ;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY truncate_02009_actor CASCADE;
DROP ROLE IF EXISTS truncate_02009_actor;
DROP TABLE IF EXISTS truncate_02009_tbl, truncate_02009_ref CASCADE;
