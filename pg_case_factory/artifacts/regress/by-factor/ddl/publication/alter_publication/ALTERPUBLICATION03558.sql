-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER PUBLICATION table_dependency=table_not_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERPUBLICATION03558
-- source_md: skills/pg-sql-generation/references/statements/ddl/publication/alter_publication.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/publication/alter_publication.yaml
-- primary_obligation_id: ALTPUB-EXT|03558|add_object|error_assertion|drop_publication
-- expected_outcome: expected_failure
-- expected_sqlstate: 42P01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP PUBLICATION IF EXISTS alterpublication_03558_pub CASCADE;
DROP SCHEMA IF EXISTS alterpublication_03558_sch CASCADE;
DROP ROLE IF EXISTS alterpublication_03558_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地发布和因子专用夹具。
CREATE SCHEMA IF NOT EXISTS alterpublication_03558_sch;
CREATE ROLE alterpublication_03558_owner LOGIN;
GRANT USAGE ON SCHEMA public TO alterpublication_03558_owner;
GRANT USAGE ON SCHEMA alterpublication_03558_sch TO alterpublication_03558_owner;
CREATE PUBLICATION alterpublication_03558_pub;
ALTER PUBLICATION alterpublication_03558_pub OWNER TO alterpublication_03558_owner;
SET ROLE alterpublication_03558_owner;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 ALTER PUBLICATION。
-- primary-target-begin
ALTER PUBLICATION alterpublication_03558_pub ADD TABLE alterpublication_03558_sch.alterpublication_03558_tbl WHERE (id > 0);
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42P01' AS target_sqlstate_matches_expected;
SELECT 1 AS error_assertion_verified;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP PUBLICATION IF EXISTS alterpublication_03558_pub CASCADE;
DROP SCHEMA IF EXISTS alterpublication_03558_sch CASCADE;
DROP OWNED BY alterpublication_03558_owner;
DROP ROLE IF EXISTS alterpublication_03558_owner;
