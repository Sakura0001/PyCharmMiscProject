-- TC-018：failover 期间存在未完成 split TLB
--
-- 用例内容
-- 优先级:
--   P0
-- 场景类型:
--   可靠性
-- 前置条件:
--   主备/只读拓扑可执行 failover，LargeSLB 正在 flush
-- 测试步骤:
--   1. 触发 LargeSLB 并延迟部分 split TLB。
--   2. 在 flush 未完全完成时发起 failover。
--   3. 新主拉起后执行一致性校验。
-- 预期结果:
--   failover 不选择 unsafe LSN 作为可见边界；新主正常服务；数据无丢失、无半事务。
-- 验证点:
--   倒换 LSN、恢复边界、拓扑一致性。
--
-- LargeSLB 执行前推荐参数:
--   当前内核查询范围:
--     innodb_log_write_max_size: 0 - 524288，推荐取最大值 524288
--     innodb_log_write_min_time_interval: 0 - 18446744073709551615，推荐取 1000000
--     innodb_log_write_min_size: 0 - 131072，推荐取最大值 131072
--   推荐公共配置:
--     SET GLOBAL innodb_log_write_max_size = 524288;
--     SET GLOBAL innodb_log_write_min_time_interval = 1000000;
--     SET GLOBAL innodb_log_write_min_size = 131072;
--   关键限制:
--     单次 redo write 最大约 512KB，不能直接聚到 2MB。
--     正向 LargeSLB 用例依赖多批 redo/GFB 在同一 slice flush session 中累计超过阈值。
--   TLB 参数 profile:
--     Profile A 真实 2MB: sal_tlb_max_size=2097152, slice_tlb_size=2097152, slice_flush_size_threshold=2097152, slice_tlb_size_max=2097152
--     Profile B 加速拆分: sal_tlb_max_size=65536, slice_tlb_size=4096, slice_flush_size_threshold=4096, slice_tlb_size_max=65536
--     TC-001 fast path 回归不要使用 Profile B。
-- 执行说明:
--   本文件为独立 SQL，会重建 largeslb_test 库中的测试表和公共存储过程。
--   SQL 负责生成达到用例规模的数据；slice、TLB、unsafe LSN、SYNC_MSG_SLICE 等需要结合内核日志/perfcounter/debug hook 验证。
--   并发、failover、CR、kill -9、磁盘满、网络断连、flush 失败等场景需要外部压测/故障注入框架；本 SQL 只提供该用例的负载入口。

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
DROP PROCEDURE IF EXISTS lgslb_tc018$$
CREATE PROCEDURE lgslb_tc018()
BEGIN
  CALL lgslb_reset_case('TC-018');
  CALL lgslb_fill('TC-018', 512, 16384, 2);
  CALL lgslb_update_bucket_range('TC-018', 0, 1, 256, 16384, 'tc018_failover');
  CALL lgslb_assert_case('TC-018', 512);
END$$
DELIMITER ;

CALL largeslb_test.lgslb_tc018();
