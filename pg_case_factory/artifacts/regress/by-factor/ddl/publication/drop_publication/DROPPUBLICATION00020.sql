-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : DROP PUBLICATION privilege_context=non_owner_no_privilege
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: DROPPUBLICATION00020
-- source_md: skills/pg-sql-generation/references/statements/ddl/publication/drop_publication.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/publication/drop_publication.yaml
-- primary_obligation_id: DROPPUBLICATION-SFV|sfv-aa9f518ff632cd8d10a014cd|drop_publication
-- expected_outcome: expected_failure
-- expected_sqlstate: 42501
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP PUBLICATION IF EXISTS droppublication_00020_pub;
DROP OWNED BY droppublication_00020_actor;
DROP ROLE IF EXISTS droppublication_00020_actor;
\set ON_ERROR_STOP on
-- 2. 创建完整本地发布和因子专用夹具。
CREATE ROLE droppublication_00020_actor LOGIN NOSUPERUSER;
CREATE PUBLICATION droppublication_00020_pub;
SET ROLE droppublication_00020_actor;
\set ON_ERROR_STOP off
-- 3. 执行唯一获得覆盖信用的 DROP PUBLICATION。
-- primary-target-begin
DROP PUBLICATION droppublication_00020_pub;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
\set ON_ERROR_STOP on
-- 4. 验证 SQLSTATE、目录状态和数据行为。
RESET ROLE;
SELECT :'target_sqlstate' = '42501' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS publication_present FROM pg_catalog.pg_publication WHERE pubname = 'droppublication_00020_pub' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
RESET ROLE;
DROP PUBLICATION IF EXISTS droppublication_00020_pub;
DROP OWNED BY droppublication_00020_actor;
DROP ROLE IF EXISTS droppublication_00020_actor;
