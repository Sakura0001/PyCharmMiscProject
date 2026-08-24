-- --------------------------------------------------------
-- 版权所有(C)  2021-2030 华为技术有限公司
--
-- --
-- author       : pg-case-factory Codex
-- create at    : 2026-08-06
-- version      : 1.0
-- description  : Verify PostgreSQL 18.4 CLOSE with statement_branch=branch_1, expected_status=failure, cursor_state=with_hold_after_commit, direction_shape=absolute, hold_scroll_shape=default, cursor_name_shape=plain_identifier, query_shape=ordered_select, transaction_context=after_rollback, dependency_state=missing_dependency, invalid_combination=none, position_boundary=middle, verification_mode=returned_rows, cleanup_mode=rollback
-- FE           : PG18-CURSOR-DCL
-- ++
-- --------------------------------------------------------
-- factor statement_branch=branch_1
-- factor expected_status=failure
-- factor cursor_state=with_hold_after_commit
-- factor direction_shape=absolute
-- factor hold_scroll_shape=default
-- factor cursor_name_shape=plain_identifier
-- factor query_shape=ordered_select
-- factor transaction_context=after_rollback
-- factor dependency_state=missing_dependency
-- factor invalid_combination=none
-- factor position_boundary=middle
-- factor verification_mode=returned_rows
-- factor cleanup_mode=rollback
DROP TABLE IF EXISTS cur_00149_table;
CREATE TABLE cur_00149_table (id integer PRIMARY KEY, payload text);
INSERT INTO cur_00149_table(id, payload) VALUES (1, 'alpha'), (2, 'beta'), (3, 'gamma');
BEGIN;
ROLLBACK;
DECLARE cur_00149_cursor CURSOR WITH HOLD FOR SELECT id FROM cur_00149_missing_table ORDER BY id;
CLOSE cur_00149_missing_cursor;
SELECT id, payload FROM cur_00149_table ORDER BY id;
ROLLBACK;
DROP TABLE IF EXISTS cur_00149_table;
