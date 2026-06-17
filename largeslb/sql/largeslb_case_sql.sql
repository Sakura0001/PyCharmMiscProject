-- LargeSLB case SQL helper.
-- Usage:
--   1. mysql -h127.0.0.1 -P3306 -utest -ptest < largeslb_case_sql.sql
--   2. Execute one case procedure at a time, for example: CALL largeslb_test.lgslb_tc002();
--
-- Notes:
--   - The SQL generates enough row count and payload length to trigger or approximate each case.
--   - On the current kernel, innodb_log_write_max_size is capped at 524288 bytes.
--     Therefore positive LargeSLB cases rely on multiple redo writes / GFBs being
--     accumulated in one slice flush session, not on one redo write reaching 2MB.
--   - Exact redo-record size, page-id, slice-id, unsafe LSN, TLB count, and SYNC_MSG_SLICE timing
--     still require kernel logs, perfcounters, debug hooks, or UT assertions.
--   - TC-006 is unsupported by design: a single redo record > 2MB is expected to crash.
--     It is provided as an isolated negative procedure and must not be run in shared or batch jobs.

CREATE DATABASE IF NOT EXISTS largeslb_test;
USE largeslb_test;

DROP TABLE IF EXISTS lgslb_txn_audit;
DROP TABLE IF EXISTS lgslb_payload;

CREATE TABLE lgslb_payload (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  case_id VARCHAR(16) NOT NULL,
  bucket INT NOT NULL,
  marker VARCHAR(64) NOT NULL DEFAULT '',
  payload LONGTEXT NOT NULL,
  updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_case_bucket (case_id, bucket, id),
  KEY idx_case_marker (case_id, marker)
) ENGINE=InnoDB ROW_FORMAT=DYNAMIC;

CREATE TABLE lgslb_txn_audit (
  id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT,
  case_id VARCHAR(16) NOT NULL,
  marker VARCHAR(64) NOT NULL,
  rows_touched BIGINT UNSIGNED NOT NULL,
  payload_len INT UNSIGNED NOT NULL,
  total_payload_bytes BIGINT UNSIGNED NOT NULL,
  note VARCHAR(256) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_case_marker (case_id, marker)
) ENGINE=InnoDB;

DELIMITER $$

DROP PROCEDURE IF EXISTS lgslb_reset_case$$
CREATE PROCEDURE lgslb_reset_case(IN p_case_id VARCHAR(16))
BEGIN
  DELETE FROM lgslb_txn_audit WHERE case_id = p_case_id;
  DELETE FROM lgslb_payload WHERE case_id = p_case_id;
END$$

DROP PROCEDURE IF EXISTS lgslb_fill$$
CREATE PROCEDURE lgslb_fill(
  IN p_case_id VARCHAR(16),
  IN p_rows INT UNSIGNED,
  IN p_payload_len INT UNSIGNED,
  IN p_bucket_mod INT UNSIGNED
)
BEGIN
  DECLARE i INT UNSIGNED DEFAULT 0;
  DECLARE v_payload LONGTEXT;
  DECLARE v_seed VARCHAR(64);

  SET v_seed = CONCAT(p_case_id, '_seed_');
  SET v_payload = LEFT(REPEAT(v_seed, (p_payload_len DIV GREATEST(1, CHAR_LENGTH(v_seed))) + 2), p_payload_len);

  WHILE i < p_rows DO
    INSERT INTO lgslb_payload(case_id, bucket, marker, payload)
    VALUES (p_case_id, i % GREATEST(1, p_bucket_mod), 'seed', v_payload);
    SET i = i + 1;
  END WHILE;

  INSERT INTO lgslb_txn_audit(case_id, marker, rows_touched, payload_len, total_payload_bytes, note)
  VALUES (p_case_id, 'seed', p_rows, p_payload_len, p_rows * p_payload_len, 'seed rows inserted');
END$$

DROP PROCEDURE IF EXISTS lgslb_update_rows$$
CREATE PROCEDURE lgslb_update_rows(
  IN p_case_id VARCHAR(16),
  IN p_limit INT UNSIGNED,
  IN p_payload_len INT UNSIGNED,
  IN p_marker VARCHAR(64)
)
BEGIN
  DECLARE v_payload LONGTEXT;
  DECLARE v_rows BIGINT UNSIGNED DEFAULT 0;

  SET v_payload = LEFT(REPEAT(CONCAT(p_marker, '_'), (p_payload_len DIV GREATEST(1, CHAR_LENGTH(p_marker) + 1)) + 2), p_payload_len);

  START TRANSACTION;
    UPDATE lgslb_payload
       SET payload = CONCAT(LEFT(v_payload, GREATEST(0, p_payload_len - 20)), LPAD(id, 20, '0')),
           marker = p_marker
     WHERE case_id = p_case_id
     ORDER BY id
     LIMIT p_limit;
    SET v_rows = ROW_COUNT();
    INSERT INTO lgslb_txn_audit(case_id, marker, rows_touched, payload_len, total_payload_bytes, note)
    VALUES (p_case_id, p_marker, v_rows, p_payload_len, v_rows * p_payload_len, 'single transaction update by id');
  COMMIT;
END$$

DROP PROCEDURE IF EXISTS lgslb_update_bucket$$
CREATE PROCEDURE lgslb_update_bucket(
  IN p_case_id VARCHAR(16),
  IN p_bucket INT,
  IN p_limit INT UNSIGNED,
  IN p_payload_len INT UNSIGNED,
  IN p_marker VARCHAR(64)
)
BEGIN
  DECLARE v_payload LONGTEXT;
  DECLARE v_rows BIGINT UNSIGNED DEFAULT 0;

  SET v_payload = LEFT(REPEAT(CONCAT(p_marker, '_'), (p_payload_len DIV GREATEST(1, CHAR_LENGTH(p_marker) + 1)) + 2), p_payload_len);

  START TRANSACTION;
    UPDATE lgslb_payload
       SET payload = CONCAT(LEFT(v_payload, GREATEST(0, p_payload_len - 20)), LPAD(id, 20, '0')),
           marker = p_marker
     WHERE case_id = p_case_id AND bucket = p_bucket
     ORDER BY id
     LIMIT p_limit;
    SET v_rows = ROW_COUNT();
    INSERT INTO lgslb_txn_audit(case_id, marker, rows_touched, payload_len, total_payload_bytes, note)
    VALUES (p_case_id, p_marker, v_rows, p_payload_len, v_rows * p_payload_len, CONCAT('single bucket update bucket=', p_bucket));
  COMMIT;
END$$

DROP PROCEDURE IF EXISTS lgslb_update_bucket_range$$
CREATE PROCEDURE lgslb_update_bucket_range(
  IN p_case_id VARCHAR(16),
  IN p_bucket_from INT,
  IN p_bucket_to INT,
  IN p_limit_per_bucket INT UNSIGNED,
  IN p_payload_len INT UNSIGNED,
  IN p_marker VARCHAR(64)
)
BEGIN
  DECLARE b INT DEFAULT 0;
  DECLARE v_payload LONGTEXT;
  DECLARE v_rows BIGINT UNSIGNED DEFAULT 0;
  DECLARE v_total BIGINT UNSIGNED DEFAULT 0;

  SET b = p_bucket_from;
  SET v_payload = LEFT(REPEAT(CONCAT(p_marker, '_'), (p_payload_len DIV GREATEST(1, CHAR_LENGTH(p_marker) + 1)) + 2), p_payload_len);

  START TRANSACTION;
    WHILE b <= p_bucket_to DO
      UPDATE lgslb_payload
         SET payload = CONCAT(LEFT(v_payload, GREATEST(0, p_payload_len - 20)), LPAD(id, 20, '0')),
             marker = p_marker
       WHERE case_id = p_case_id AND bucket = b
       ORDER BY id
       LIMIT p_limit_per_bucket;
      SET v_rows = ROW_COUNT();
      SET v_total = v_total + v_rows;
      SET b = b + 1;
    END WHILE;

    INSERT INTO lgslb_txn_audit(case_id, marker, rows_touched, payload_len, total_payload_bytes, note)
    VALUES (p_case_id, p_marker, v_total, p_payload_len, v_total * p_payload_len, 'single transaction update across bucket range');
  COMMIT;
END$$

DROP PROCEDURE IF EXISTS lgslb_reupdate_one_row$$
CREATE PROCEDURE lgslb_reupdate_one_row(
  IN p_case_id VARCHAR(16),
  IN p_rounds INT UNSIGNED,
  IN p_payload_len INT UNSIGNED,
  IN p_marker VARCHAR(64)
)
BEGIN
  DECLARE i INT UNSIGNED DEFAULT 0;
  DECLARE v_id BIGINT UNSIGNED DEFAULT 0;
  DECLARE v_payload LONGTEXT;

  CALL lgslb_reset_case(p_case_id);
  SET v_payload = LEFT(REPEAT(CONCAT(p_marker, '_'), (p_payload_len DIV GREATEST(1, CHAR_LENGTH(p_marker) + 1)) + 2), p_payload_len);

  INSERT INTO lgslb_payload(case_id, bucket, marker, payload)
  VALUES (p_case_id, 0, 'seed', LEFT(v_payload, 1024));
  SET v_id = LAST_INSERT_ID();

  START TRANSACTION;
    WHILE i < p_rounds DO
      UPDATE lgslb_payload
         SET payload = CONCAT(LEFT(v_payload, GREATEST(0, p_payload_len - 20)), LPAD(i, 20, '0')),
             marker = p_marker
       WHERE id = v_id;
      SET i = i + 1;
    END WHILE;
    INSERT INTO lgslb_txn_audit(case_id, marker, rows_touched, payload_len, total_payload_bytes, note)
    VALUES (p_case_id, p_marker, p_rounds, p_payload_len, p_rounds * p_payload_len, 'repeat update one row to approximate same page-id compact records');
  COMMIT;
END$$

DROP PROCEDURE IF EXISTS lgslb_assert_case$$
CREATE PROCEDURE lgslb_assert_case(IN p_case_id VARCHAR(16), IN p_min_rows INT UNSIGNED)
BEGIN
  SELECT
    p_case_id AS case_id,
    COUNT(*) AS row_count,
    MIN(OCTET_LENGTH(payload)) AS min_payload_len,
    MAX(OCTET_LENGTH(payload)) AS max_payload_len,
    SUM(OCTET_LENGTH(payload)) AS total_payload_bytes,
    SUM(CAST(CRC32(CONCAT(id, ':', marker, ':', LEFT(payload, 64), ':', RIGHT(payload, 64))) AS UNSIGNED)) AS light_checksum
  FROM lgslb_payload
  WHERE case_id = p_case_id;

  SELECT
    case_id,
    marker,
    rows_touched,
    payload_len,
    total_payload_bytes,
    note,
    created_at
  FROM lgslb_txn_audit
  WHERE case_id = p_case_id
  ORDER BY id;

  SELECT
    CASE WHEN COUNT(*) >= p_min_rows THEN 'PASS_ROW_COUNT' ELSE 'FAIL_ROW_COUNT' END AS row_count_check,
    COUNT(*) AS actual_rows,
    p_min_rows AS expected_min_rows
  FROM lgslb_payload
  WHERE case_id = p_case_id;
END$$

DROP PROCEDURE IF EXISTS lgslb_tc001$$
CREATE PROCEDURE lgslb_tc001()
BEGIN
  CALL lgslb_reset_case('TC-001');
  CALL lgslb_fill('TC-001', 1000, 512, 16);
  CALL lgslb_update_rows('TC-001', 100, 1024, 'tc001_fast');
  CALL lgslb_assert_case('TC-001', 1000);
END$$

DROP PROCEDURE IF EXISTS lgslb_tc002$$
CREATE PROCEDURE lgslb_tc002()
BEGIN
  CALL lgslb_reset_case('TC-002');
  CALL lgslb_fill('TC-002', 192, 32768, 1);
  CALL lgslb_update_bucket('TC-002', 0, 160, 32768, 'tc002_single_slice');
  CALL lgslb_assert_case('TC-002', 192);
END$$

DROP PROCEDURE IF EXISTS lgslb_tc003$$
CREATE PROCEDURE lgslb_tc003()
BEGIN
  CALL lgslb_reset_case('TC-003');
  CALL lgslb_fill('TC-003', 384, 16384, 1);
  CALL lgslb_update_bucket('TC-003', 0, 96, 16384, 'tc003_gfb_1');
  CALL lgslb_update_bucket('TC-003', 0, 96, 16384, 'tc003_gfb_2');
  CALL lgslb_update_bucket('TC-003', 0, 96, 16384, 'tc003_gfb_3');
  CALL lgslb_assert_case('TC-003', 384);
END$$

DROP PROCEDURE IF EXISTS lgslb_tc004$$
CREATE PROCEDURE lgslb_tc004()
BEGIN
  CALL lgslb_reupdate_one_row('TC-004', 96, 32768, 'tc004_same_page');
  CALL lgslb_assert_case('TC-004', 1);
END$$

DROP PROCEDURE IF EXISTS lgslb_tc005$$
CREATE PROCEDURE lgslb_tc005()
BEGIN
  CALL lgslb_reset_case('TC-005');
  CALL lgslb_fill('TC-005', 1600, 1024, 4);
  CALL lgslb_update_rows('TC-005', 511, 4096, 'tc005_2m_minus');
  CALL lgslb_update_rows('TC-005', 512, 4096, 'tc005_2m_equal');
  CALL lgslb_update_rows('TC-005', 513, 4096, 'tc005_2m_plus');
  CALL lgslb_assert_case('TC-005', 1600);
END$$

DROP PROCEDURE IF EXISTS lgslb_tc006_unsupported_single_redo_crash$$
CREATE PROCEDURE lgslb_tc006_unsupported_single_redo_crash()
BEGIN
  CALL lgslb_reset_case('TC-006');
  CALL lgslb_fill('TC-006', 1, 1024, 1);
  CALL lgslb_update_rows('TC-006', 1, 2200000, 'tc006_single_redo_gt2m');
  CALL lgslb_assert_case('TC-006', 1);
END$$

DROP PROCEDURE IF EXISTS lgslb_tc007$$
CREATE PROCEDURE lgslb_tc007()
BEGIN
  CALL lgslb_reset_case('TC-007');
  CALL lgslb_fill('TC-007', 512, 8192, 8);
  CALL lgslb_update_bucket('TC-007', 5, 64, 8192, 'tc007_order_5');
  CALL lgslb_update_bucket('TC-007', 2, 64, 8192, 'tc007_order_2');
  CALL lgslb_update_bucket('TC-007', 7, 64, 8192, 'tc007_order_7');
  CALL lgslb_update_bucket('TC-007', 0, 64, 8192, 'tc007_order_0');
  CALL lgslb_assert_case('TC-007', 512);
END$$

DROP PROCEDURE IF EXISTS lgslb_tc008$$
CREATE PROCEDURE lgslb_tc008()
BEGIN
  CALL lgslb_reset_case('TC-008');
  CALL lgslb_fill('TC-008', 768, 16384, 4);
  CALL lgslb_update_bucket_range('TC-008', 0, 3, 96, 16384, 'tc008_multi_slice');
  CALL lgslb_assert_case('TC-008', 768);
END$$

DROP PROCEDURE IF EXISTS lgslb_tc009$$
CREATE PROCEDURE lgslb_tc009()
BEGIN
  CALL lgslb_reset_case('TC-009');
  CALL lgslb_fill('TC-009', 960, 8192, 6);
  CALL lgslb_update_rows('TC-009', 32, 8192, 'tc009_no_split');
  CALL lgslb_update_bucket('TC-009', 0, 256, 8192, 'tc009_single_split');
  CALL lgslb_update_bucket_range('TC-009', 1, 5, 128, 8192, 'tc009_multi_split');
  CALL lgslb_assert_case('TC-009', 960);
END$$

DROP PROCEDURE IF EXISTS lgslb_tc010$$
CREATE PROCEDURE lgslb_tc010()
BEGIN
  CALL lgslb_reset_case('TC-010');
  CALL lgslb_fill('TC-010', 260, 8192, 1);
  CALL lgslb_update_rows('TC-010', 10, 4096, 'tc010_prefill');
  CALL lgslb_update_bucket('TC-010', 0, 240, 8192, 'tc010_force_flush');
  CALL lgslb_assert_case('TC-010', 260);
END$$

DROP PROCEDURE IF EXISTS lgslb_tc011$$
CREATE PROCEDURE lgslb_tc011()
BEGIN
  CALL lgslb_reupdate_one_row('TC-011', 128, 24576, 'tc011_pmp_continue');
  CALL lgslb_assert_case('TC-011', 1);
END$$

DROP PROCEDURE IF EXISTS lgslb_tc012$$
CREATE PROCEDURE lgslb_tc012()
BEGIN
  CALL lgslb_reset_case('TC-012');
  CALL lgslb_fill('TC-012', 320, 24576, 1);
  CALL lgslb_update_bucket('TC-012', 0, 256, 24576, 'tc012_redo_buffer_hold');
  CALL lgslb_assert_case('TC-012', 320);
END$$

DROP PROCEDURE IF EXISTS lgslb_tc013$$
CREATE PROCEDURE lgslb_tc013()
BEGIN
  CALL lgslb_reset_case('TC-013');
  CALL lgslb_fill('TC-013', 384, 16384, 1);
  CALL lgslb_update_bucket('TC-013', 0, 384, 16384, 'tc013_three_tlb_guard');
  CALL lgslb_assert_case('TC-013', 384);
END$$

DROP PROCEDURE IF EXISTS lgslb_tc014$$
CREATE PROCEDURE lgslb_tc014()
BEGIN
  CALL lgslb_reset_case('TC-014');
  CALL lgslb_fill('TC-014', 384, 16384, 2);
  CALL lgslb_update_bucket('TC-014', 0, 192, 16384, 'tc014_completion_handler');
  CALL lgslb_update_bucket('TC-014', 1, 192, 16384, 'tc014_lsn_watcher');
  CALL lgslb_assert_case('TC-014', 384);
END$$

DROP PROCEDURE IF EXISTS lgslb_tc015$$
CREATE PROCEDURE lgslb_tc015()
BEGIN
  CALL lgslb_reset_case('TC-015');
  CALL lgslb_fill('TC-015', 448, 16384, 1);
  CALL lgslb_update_bucket('TC-015', 0, 448, 16384, 'tc015_sync_wait_all');
  CALL lgslb_assert_case('TC-015', 448);
END$$

DROP PROCEDURE IF EXISTS lgslb_tc016$$
CREATE PROCEDURE lgslb_tc016()
BEGIN
  CALL lgslb_reset_case('TC-016');
  CALL lgslb_fill('TC-016', 512, 16384, 4);
  CALL lgslb_update_bucket_range('TC-016', 0, 3, 96, 16384, 'tc016_ro_safe_cv');
  CALL lgslb_assert_case('TC-016', 512);
END$$

DROP PROCEDURE IF EXISTS lgslb_tc017$$
CREATE PROCEDURE lgslb_tc017()
BEGIN
  CALL lgslb_reset_case('TC-017');
  CALL lgslb_fill('TC-017', 640, 8192, 4);
  CALL lgslb_update_bucket_range('TC-017', 0, 3, 160, 8192, 'tc017_recycle_release');
  CALL lgslb_assert_case('TC-017', 640);
END$$

DROP PROCEDURE IF EXISTS lgslb_tc018$$
CREATE PROCEDURE lgslb_tc018()
BEGIN
  CALL lgslb_reset_case('TC-018');
  CALL lgslb_fill('TC-018', 512, 16384, 2);
  CALL lgslb_update_bucket_range('TC-018', 0, 1, 256, 16384, 'tc018_failover');
  CALL lgslb_assert_case('TC-018', 512);
END$$

DROP PROCEDURE IF EXISTS lgslb_tc019$$
CREATE PROCEDURE lgslb_tc019()
BEGIN
  CALL lgslb_reset_case('TC-019');
  CALL lgslb_fill('TC-019', 512, 16384, 2);
  CALL lgslb_update_bucket_range('TC-019', 0, 1, 256, 16384, 'tc019_cr_start');
  CALL lgslb_assert_case('TC-019', 512);
END$$

DROP PROCEDURE IF EXISTS lgslb_tc020$$
CREATE PROCEDURE lgslb_tc020()
BEGIN
  CALL lgslb_reset_case('TC-020');
  CALL lgslb_fill('TC-020', 512, 16384, 2);
  CALL lgslb_update_bucket_range('TC-020', 0, 1, 256, 16384, 'tc020_gap_fill');
  CALL lgslb_assert_case('TC-020', 512);
END$$

DROP PROCEDURE IF EXISTS lgslb_tc021$$
CREATE PROCEDURE lgslb_tc021()
BEGIN
  CALL lgslb_reset_case('TC-021');
  CALL lgslb_fill('TC-021', 768, 16384, 1);
  CALL lgslb_update_bucket('TC-021', 0, 512, 16384, 'tc021_version_replace');
  CALL lgslb_assert_case('TC-021', 768);
END$$

DROP PROCEDURE IF EXISTS lgslb_tc022$$
CREATE PROCEDURE lgslb_tc022()
BEGIN
  CALL lgslb_reset_case('TC-022');
  CALL lgslb_fill('TC-022', 640, 16384, 1);
  CALL lgslb_update_bucket('TC-022', 0, 320, 16384, 'tc022_enable_off_on');
  CALL lgslb_assert_case('TC-022', 640);
END$$

DROP PROCEDURE IF EXISTS lgslb_tc023$$
CREATE PROCEDURE lgslb_tc023()
BEGIN
  CALL lgslb_reset_case('TC-023');
  CALL lgslb_fill('TC-023', 512, 4096, 4);
  CALL lgslb_update_rows('TC-023', 64, 4096, 'tc023_4k');
  CALL lgslb_update_rows('TC-023', 64, 65536, 'tc023_64k');
  CALL lgslb_update_rows('TC-023', 2, 1048576, 'tc023_1m_sample');
  CALL lgslb_assert_case('TC-023', 512);
END$$

DROP PROCEDURE IF EXISTS lgslb_tc024$$
CREATE PROCEDURE lgslb_tc024()
BEGIN
  CALL lgslb_reset_case('TC-024');
  CALL lgslb_fill('TC-024', 1100, 4096, 5);
  CALL lgslb_update_bucket('TC-024', 0, 32, 4096, 'tc024_64k');
  CALL lgslb_update_bucket('TC-024', 1, 64, 4096, 'tc024_128k');
  CALL lgslb_update_bucket('TC-024', 2, 160, 4096, 'tc024_512k');
  CALL lgslb_update_bucket('TC-024', 3, 320, 4096, 'tc024_1m');
  CALL lgslb_update_bucket('TC-024', 4, 513, 4096, 'tc024_2m_plus');
  CALL lgslb_assert_case('TC-024', 1100);
END$$

DROP PROCEDURE IF EXISTS lgslb_tc025$$
CREATE PROCEDURE lgslb_tc025()
BEGIN
  CALL lgslb_reset_case('TC-025');
  CALL lgslb_fill('TC-025', 512, 16384, 1);
  CALL lgslb_update_bucket('TC-025', 0, 512, 16384, 'tc025_flush_retry');
  CALL lgslb_assert_case('TC-025', 512);
END$$

DROP PROCEDURE IF EXISTS lgslb_tc026$$
CREATE PROCEDURE lgslb_tc026()
BEGIN
  CALL lgslb_reset_case('TC-026');
  CALL lgslb_fill('TC-026', 512, 16384, 1);
  CALL lgslb_update_bucket('TC-026', 0, 512, 16384, 'tc026_crash_replay');
  CALL lgslb_assert_case('TC-026', 512);
END$$

DROP PROCEDURE IF EXISTS lgslb_tc027$$
CREATE PROCEDURE lgslb_tc027()
BEGIN
  CALL lgslb_reset_case('TC-027');
  CALL lgslb_fill('TC-027', 512, 16384, 1);
  CALL lgslb_update_bucket('TC-027', 0, 512, 16384, 'tc027_disk_full');
  CALL lgslb_assert_case('TC-027', 512);
END$$

DROP PROCEDURE IF EXISTS lgslb_tc028$$
CREATE PROCEDURE lgslb_tc028()
BEGIN
  CALL lgslb_reset_case('TC-028');
  CALL lgslb_fill('TC-028', 512, 16384, 4);
  CALL lgslb_update_bucket_range('TC-028', 0, 3, 128, 16384, 'tc028_network_replica');
  CALL lgslb_assert_case('TC-028', 512);
END$$

DROP PROCEDURE IF EXISTS lgslb_tc029$$
CREATE PROCEDURE lgslb_tc029()
BEGIN
  CALL lgslb_reset_case('TC-029');
  CALL lgslb_fill('TC-029', 1024, 8192, 4);
  CALL lgslb_update_bucket_range('TC-029', 0, 3, 256, 8192, 'tc029_longrun_round1');
  CALL lgslb_update_bucket_range('TC-029', 0, 3, 256, 8192, 'tc029_longrun_round2');
  CALL lgslb_assert_case('TC-029', 1024);
END$$

DROP PROCEDURE IF EXISTS lgslb_tc030$$
CREATE PROCEDURE lgslb_tc030()
BEGIN
  CALL lgslb_reset_case('TC-030');
  CALL lgslb_fill('TC-030', 1280, 8192, 8);
  CALL lgslb_update_bucket('TC-030', 0, 256, 16384, 'tc030_large_20pct');
  CALL lgslb_update_bucket_range('TC-030', 1, 7, 80, 2048, 'tc030_small_80pct');
  CALL lgslb_assert_case('TC-030', 1280);
END$$

DELIMITER ;

-- Suggested one-case-at-a-time execution:
-- CALL largeslb_test.lgslb_tc001();
-- CALL largeslb_test.lgslb_tc002();
-- CALL largeslb_test.lgslb_tc003();
-- CALL largeslb_test.lgslb_tc004();
-- CALL largeslb_test.lgslb_tc005();
-- TC-006 is unsupported and expected to crash. Run only in an isolated disposable instance:
-- CALL largeslb_test.lgslb_tc006_unsupported_single_redo_crash();
-- CALL largeslb_test.lgslb_tc007();
-- CALL largeslb_test.lgslb_tc008();
-- CALL largeslb_test.lgslb_tc009();
-- CALL largeslb_test.lgslb_tc010();
-- CALL largeslb_test.lgslb_tc011();
-- CALL largeslb_test.lgslb_tc012();
-- CALL largeslb_test.lgslb_tc013();
-- CALL largeslb_test.lgslb_tc014();
-- CALL largeslb_test.lgslb_tc015();
-- CALL largeslb_test.lgslb_tc016();
-- CALL largeslb_test.lgslb_tc017();
-- CALL largeslb_test.lgslb_tc018();
-- CALL largeslb_test.lgslb_tc019();
-- CALL largeslb_test.lgslb_tc020();
-- CALL largeslb_test.lgslb_tc021();
-- CALL largeslb_test.lgslb_tc022();
-- CALL largeslb_test.lgslb_tc023();
-- CALL largeslb_test.lgslb_tc024();
-- CALL largeslb_test.lgslb_tc025();
-- CALL largeslb_test.lgslb_tc026();
-- CALL largeslb_test.lgslb_tc027();
-- CALL largeslb_test.lgslb_tc028();
-- CALL largeslb_test.lgslb_tc029();
-- CALL largeslb_test.lgslb_tc030();
