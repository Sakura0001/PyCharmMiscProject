-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 MOVE with statement_branch=branch_1, expected_status=failure, cursor_state=with_hold_after_commit, direction_shape=absolute, hold_scroll_shape=no_scroll, cursor_name_shape=plain_identifier, query_shape=ordered_select, transaction_context=outside_transaction, dependency_state=missing_dependency, invalid_combination=syntax_valid_semantic_error, position_boundary=middle, verification_mode=returned_rows, cleanup_mode=drop_objects
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor cursor_state=with_hold_after_commit
-- factor direction_shape=absolute
-- factor hold_scroll_shape=no_scroll
-- factor cursor_name_shape=plain_identifier
-- factor query_shape=ordered_select
-- factor transaction_context=outside_transaction
-- factor dependency_state=missing_dependency
-- factor invalid_combination=syntax_valid_semantic_error
-- factor position_boundary=middle
-- factor verification_mode=returned_rows
-- factor cleanup_mode=drop_objects
DROP TABLE IF EXISTS cur_00657_table;
CREATE TABLE cur_00657_table (id integer PRIMARY KEY, payload text);
INSERT INTO cur_00657_table(id, payload) VALUES (1, 'alpha'), (2, 'beta'), (3, 'gamma');
DECLARE cur_00657_cursor NO SCROLL CURSOR WITH HOLD FOR SELECT id FROM cur_00657_missing_table ORDER BY id;
MOVE ABSOLUTE 2 FROM cur_00657_missing_cursor;
SELECT 1 AS failure_boundary;
SELECT id, payload FROM cur_00657_table ORDER BY id;
COMMIT;
DROP TABLE IF EXISTS cur_00657_table;
