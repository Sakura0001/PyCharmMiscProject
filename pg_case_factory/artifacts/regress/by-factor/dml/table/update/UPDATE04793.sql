-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : UPDATE privilege_context=insufficient_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: UPDATE04793
-- source_md: skills/pg-sql-generation/references/statements/dml/table/update.md
-- factor_md: skills/pg-sql-generation/references/combinations/dml/table/update.yaml
-- primary_obligation_id: UPDATE-EXT|04793|catalog_query|reset_state
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS update_04793_tbl, update_04793_src, update_04793_ref CASCADE;
RESET ROLE;
DROP OWNED BY update_04793_actor CASCADE;
DROP ROLE IF EXISTS update_04793_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
CREATE ROLE update_04793_actor LOGIN NOSUPERUSER;
CREATE TABLE update_04793_tbl (id int, val int);
INSERT INTO update_04793_tbl VALUES (1, 100), (2, 200);
CREATE TABLE update_04793_src (val int);
INSERT INTO update_04793_src VALUES (1);
GRANT SELECT ON update_04793_tbl TO update_04793_actor;
SET ROLE update_04793_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 UPDATE。
-- primary-target-begin
UPDATE public.update_04793_tbl SET val = (SELECT val FROM update_04793_src) WHERE id = 1;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS relation_state FROM pg_catalog.pg_class WHERE relname = 'update_04793_tbl' AND relkind = 'r' ORDER BY count(*);
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP OWNED BY update_04793_actor CASCADE;
DROP ROLE IF EXISTS update_04793_actor;
DROP TABLE IF EXISTS update_04793_tbl, update_04793_src, update_04793_ref CASCADE;
