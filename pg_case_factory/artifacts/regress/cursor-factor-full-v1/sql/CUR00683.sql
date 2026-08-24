-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 CLOSE with statement_branch=branch_1, expected_status=success, cursor_state=with_hold_after_commit, direction_shape=next, hold_scroll_shape=with_hold, cursor_name_shape=plain_identifier, query_shape=simple_select, transaction_context=inside_transaction, dependency_state=ready, invalid_combination=none, position_boundary=middle, verification_mode=returned_rows, cleanup_mode=rollback
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=success
-- factor cursor_state=with_hold_after_commit
-- factor direction_shape=next
-- factor hold_scroll_shape=with_hold
-- factor cursor_name_shape=plain_identifier
-- factor query_shape=simple_select
-- factor transaction_context=inside_transaction
-- factor dependency_state=ready
-- factor invalid_combination=none
-- factor position_boundary=middle
-- factor verification_mode=returned_rows
-- factor cleanup_mode=rollback
DROP TABLE IF EXISTS cur_00683_table;
CREATE TABLE cur_00683_table (id integer PRIMARY KEY, payload text);
INSERT INTO cur_00683_table(id, payload) VALUES (1, 'alpha'), (2, 'beta'), (3, 'gamma');
BEGIN;
DECLARE cur_00683_cursor CURSOR WITH HOLD FOR SELECT id, payload FROM cur_00683_table ORDER BY id;
COMMIT;
BEGIN;
MOVE NEXT FROM cur_00683_cursor;
CLOSE cur_00683_cursor;
SELECT count(*) = 0 AS cursor_closed FROM pg_catalog.pg_cursors WHERE name = 'cur_00683_cursor' ORDER BY cursor_closed;
SELECT id, payload FROM cur_00683_table ORDER BY id;
ROLLBACK;
DROP TABLE IF EXISTS cur_00683_table;
