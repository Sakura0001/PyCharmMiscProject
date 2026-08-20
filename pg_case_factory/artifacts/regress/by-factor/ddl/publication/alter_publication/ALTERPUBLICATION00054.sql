-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : codex
-- create at    : 2026-08-20
-- version      : 1.0
-- description  : ALTER PUBLICATION owner_to_clause=explicit_role_name
-- FE           : PG18-STATEMENT-FACTOR-LOOP
-- ++
-- --------------------------------------------------------
-- case_id: ALTERPUBLICATION00054
-- source_md: skills/pg-sql-generation/references/statements/ddl/publication/alter_publication.md
-- factor_md: skills/pg-sql-generation/references/combinations/ddl/publication/alter_publication.yaml
-- primary_obligation_id: ALTPUB-SFV|sfv-09da62c1601ccd3fdd611d77|owner
-- expected_outcome: success
-- expected_sqlstate: 00000
-- 1. 清理本编号对象，保证脚本可重复执行。
DROP TABLE IF EXISTS alterpublication_00054_tbl CASCADE;
DROP PUBLICATION IF EXISTS alterpublication_00054_pub CASCADE;
DROP ROLE IF EXISTS alterpublication_00054_new_owner;
\set ON_ERROR_STOP on
-- 2. 创建完整本地发布和因子专用夹具。
CREATE ROLE alterpublication_00054_new_owner LOGIN;
CREATE PUBLICATION alterpublication_00054_pub;
CREATE TABLE alterpublication_00054_tbl (id integer, data text);
-- 3. 执行唯一获得覆盖信用的 ALTER PUBLICATION。
-- primary-target-begin
ALTER PUBLICATION alterpublication_00054_pub OWNER TO alterpublication_00054_new_owner;
-- primary-target-end
\set target_sqlstate :SQLSTATE
\echo PGCF_TARGET_SQLSTATE=:target_sqlstate
-- 4. 验证 SQLSTATE、目录状态和数据行为。
SELECT :'target_sqlstate' = '00000' AS target_sqlstate_matches_expected;
SELECT pub.pubname FROM pg_catalog.pg_publication AS pub WHERE pub.pubname = 'alterpublication_00054_pub' ORDER BY pub.pubname;
-- 5. 清理全部本编号对象。
DROP PUBLICATION IF EXISTS alterpublication_00054_pub CASCADE;
DROP OWNED BY alterpublication_00054_new_owner;
DROP ROLE IF EXISTS alterpublication_00054_new_owner;
DROP TABLE IF EXISTS alterpublication_00054_tbl CASCADE;
