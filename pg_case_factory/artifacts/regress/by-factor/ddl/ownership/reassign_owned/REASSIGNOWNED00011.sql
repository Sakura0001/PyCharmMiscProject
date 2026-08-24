-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : REASSIGN OWNED multi_old_role=multiple_old_roles
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: REASSIGNOWNED00011
-- source_md: skills/pg-sql-generation/references/statements/ddl/ownership/reassign_owned.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/ownership/reassign_owned.yaml
-- primary_obligation_id: REASSIGNOWNED-SFV|sfv-03ac38d78a3d59e700f7cd59|reassign_owned
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS reassignowned_00011_t CASCADE;
DROP OWNED BY reassignowned_00011_old;
DROP OWNED BY reassignowned_00011_new;
DROP ROLE IF EXISTS reassignowned_00011_old;
DROP ROLE IF EXISTS reassignowned_00011_new;
DROP OWNED BY reassignowned_00011_old2;
DROP ROLE IF EXISTS reassignowned_00011_old2;
\set ON_ERROR_STOP on
-- 2. 创建完整本地角色和因子专用夹具。
CREATE ROLE reassignowned_00011_old LOGIN;
CREATE ROLE reassignowned_00011_old2 LOGIN;
CREATE ROLE reassignowned_00011_new LOGIN;
CREATE TABLE reassignowned_00011_t (c integer);
ALTER TABLE reassignowned_00011_t OWNER TO reassignowned_00011_old;
-- 3. 执行唯一获得覆盖信用的 REASSIGN OWNED。
-- primary-target-begin
REASSIGN OWNED BY reassignowned_00011_old, reassignowned_00011_old2 TO reassignowned_00011_new;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT count(*) > 0 AS ownership_transferred FROM pg_catalog.pg_class AS c JOIN pg_catalog.pg_roles AS r ON c.relowner = r.oid WHERE c.relname = 'reassignowned_00011_t' AND r.rolname = 'reassignowned_00011_new' ORDER BY count(*) LIMIT 1;
-- 5. 清理全部本编号对象。
DROP OWNED BY reassignowned_00011_old;
DROP OWNED BY reassignowned_00011_new;
DROP ROLE IF EXISTS reassignowned_00011_old;
DROP ROLE IF EXISTS reassignowned_00011_new;
DROP OWNED BY reassignowned_00011_old2;
DROP ROLE IF EXISTS reassignowned_00011_old2;
DROP TABLE IF EXISTS reassignowned_00011_t CASCADE;
