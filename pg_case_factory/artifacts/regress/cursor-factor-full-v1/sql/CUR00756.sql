-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 DECLARE with statement_branch=branch_1, expected_status=failure, cursor_state=declared_open, direction_shape=next, hold_scroll_shape=default, cursor_name_shape=plain_identifier, query_shape=simple_select, transaction_context=after_rollback, dependency_state=ready, invalid_combination=none, position_boundary=middle, verification_mode=returned_rows, cleanup_mode=rollback
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor cursor_state=declared_open
-- factor direction_shape=next
-- factor hold_scroll_shape=default
-- factor cursor_name_shape=plain_identifier
-- factor query_shape=simple_select
-- factor transaction_context=after_rollback
-- factor dependency_state=ready
-- factor invalid_combination=none
-- factor position_boundary=middle
-- factor verification_mode=returned_rows
-- factor cleanup_mode=rollback
DROP TABLE IF EXISTS cur_00756_table;
CREATE TABLE cur_00756_table (id integer PRIMARY KEY, payload text);
INSERT INTO cur_00756_table(id, payload) VALUES (1, 'alpha'), (2, 'beta'), (3, 'gamma');
BEGIN;
ROLLBACK;
DECLARE cur_00756_cursor CURSOR FOR SELECT id, payload FROM cur_00756_table ORDER BY id;
DECLARE cur_00756_cursor CURSOR FOR SELECT id, payload FROM cur_00756_table ORDER BY id;
SELECT id, payload FROM cur_00756_table ORDER BY id;
ROLLBACK;
DROP TABLE IF EXISTS cur_00756_table;
