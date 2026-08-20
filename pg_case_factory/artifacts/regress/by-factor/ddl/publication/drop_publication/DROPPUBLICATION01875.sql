-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP PUBLICATION subscription_dependency=has_subscription_dependency
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPPUBLICATION01875
-- source_md: skills/pg-sql-generation/references/statements/ddl/publication/drop_publication.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/publication/drop_publication.yaml
-- primary_obligation_id: DROPPUBLICATION-EXT|01875|drop_publication|error_assertion|drop_publication_cascade
-- expected_outcome: expected_failure
-- expected_sqlstate: 2BP01
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP SUBSCRIPTION IF EXISTS droppublication_01875_sub;
DROP PUBLICATION IF EXISTS "droppublication_01875_all";
\set ON_ERROR_STOP on
-- 2. 创建完整本地发布和因子专用夹具。
SELECT 1 AS target_publication_intentionally_absent;
CREATE SUBSCRIPTION droppublication_01875_sub CONNECTION 'host=localhost port=5432 dbname=pgcf' PUBLICATION "droppublication_01875_all";
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP PUBLICATION。
-- primary-target-begin
DROP PUBLICATION IF EXISTS "droppublication_01875_all" RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '2BP01' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS publication_absent FROM pg_catalog.pg_publication WHERE pubname = 'droppublication_01875_all' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP SUBSCRIPTION IF EXISTS droppublication_01875_sub;
DROP PUBLICATION IF EXISTS "droppublication_01875_all";
