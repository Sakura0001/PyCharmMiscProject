-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP PUBLICATION publication_existence=publication_exists
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPPUBLICATION01407
-- source_md: skills/pg-sql-generation/references/statements/ddl/publication/drop_publication.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/publication/drop_publication.yaml
-- primary_obligation_id: DROPPUBLICATION-EXT|01407|drop_publication|error_assertion|drop_publication_cascade
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP PUBLICATION IF EXISTS "droppublication_01407_QuotedPub";
DROP PUBLICATION IF EXISTS droppublication_01407_pub2;
\set ON_ERROR_STOP on
-- 2. 创建完整本地发布和因子专用夹具。
SELECT 1 AS target_publication_intentionally_absent;
-- 3. 执行唯一获得覆盖信用的 DROP PUBLICATION。
-- primary-target-begin
DROP PUBLICATION IF EXISTS "droppublication_01407_QuotedPub", droppublication_01407_pub2;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS publication_absent FROM pg_catalog.pg_publication WHERE pubname = 'droppublication_01407_QuotedPub' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP PUBLICATION IF EXISTS "droppublication_01407_QuotedPub";
DROP PUBLICATION IF EXISTS droppublication_01407_pub2;
