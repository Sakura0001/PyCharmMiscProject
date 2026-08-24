-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-21
-- version      : 1.0
-- description  : DROP TEXT SEARCH PARSER object_state=absent
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPTEXTSEARCHPARSER00536
-- source_md: skills/pg-sql-generation/references/statements/ddl/text_search_parser/drop_text_search_parser.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/text_search_parser/drop_text_search_parser.yaml
-- primary_obligation_id: DROPTEXTSEARCHPARSER-EXT|00536|drop_text_search_parser|catalog_query|manual_dependency_cleanup
-- expected_outcome: expected_failure
-- expected_sqlstate: 42704
-- 1. 清理本编号对象，保证脚本可重复执行。
SELECT 1 AS residual_check_no_objects;
\set ON_ERROR_STOP on
-- 2. 创建完整本地解析器和因子专用夹具。
SELECT 1 AS setup_boundary;
SELECT 1 AS target_parser_intentionally_absent;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP TEXT SEARCH PARSER。
-- primary-target-begin
DROP TEXT SEARCH PARSER "droptextsearchparser_00536_qparser" CASCADE;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '42704' AS target_sqlstate_matches_expected;
SELECT count(*) = 0 AS parser_absent FROM pg_catalog.pg_ts_parser WHERE prsname = 'droptextsearchparser_00536_qparser' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
SELECT 1 AS residual_check_no_objects;
