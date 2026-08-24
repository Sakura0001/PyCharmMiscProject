-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : CREATE DOMAIN target_action=create_domain
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: CREATEDOMAIN01814
-- source_md: skills/pg-sql-generation/references/statements/ddl/domain/create_domain.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/domain/create_domain.yaml
-- primary_obligation_id: CD-EXT|01814|catalog_query_pg_type|drop_domain
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP DOMAIN IF EXISTS createdomain_01814_dom;
\set ON_ERROR_STOP on
-- 2. 创建完整本地规则和因子专用夹具。
-- 3. 执行唯一获得覆盖信用的 CREATE DOMAIN。
-- primary-target-begin
CREATE DOMAIN createdomain_01814_dom AS smallint DEFAULT NULL CONSTRAINT createdomain_01814_chk NULL;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS domain_state FROM pg_catalog.pg_type WHERE typname = 'createdomain_01814_dom' AND typtype = 'd' ORDER BY count(*);
-- 5. 清理全部本编号对象。
DROP DOMAIN IF EXISTS createdomain_01814_dom;
