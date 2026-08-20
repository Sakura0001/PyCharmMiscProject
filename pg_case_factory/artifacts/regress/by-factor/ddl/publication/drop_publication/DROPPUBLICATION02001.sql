-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP PUBLICATION multi_target=multi_target_some_not_exist
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPPUBLICATION02001
-- source_md: skills/pg-sql-generation/references/statements/ddl/publication/drop_publication.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/publication/drop_publication.yaml
-- primary_obligation_id: DROPPUBLICATION-EXT|02001|drop_publication|pg_publication_catalog|drop_publication_cascade
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP PUBLICATION IF EXISTS droppublication_02001_pub;
DROP PUBLICATION IF EXISTS droppublication_02001_pub2;
\set ON_ERROR_STOP on
-- 2. 创建完整本地发布和因子专用夹具。
CREATE PUBLICATION droppublication_02001_pub;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP PUBLICATION。
-- primary-target-begin
DROP PUBLICATION droppublication_02001_pub, droppublication_02001_pub2 RESTRICT;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS publication_present FROM pg_catalog.pg_publication WHERE pubname = 'droppublication_02001_pub' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP PUBLICATION IF EXISTS droppublication_02001_pub;
DROP PUBLICATION IF EXISTS droppublication_02001_pub2;
