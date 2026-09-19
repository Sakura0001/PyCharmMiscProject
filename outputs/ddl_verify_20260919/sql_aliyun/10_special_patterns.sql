-- ============================================================
-- RDS MySQL DDL 秒级/在线修改列类型 测试套件 — 阿里云环境
-- 环境说明: 所有功能开关默认开启
-- 覆盖类型: 整数(SIGNED/UNSIGNED) + CHAR + VARCHAR
-- 覆盖算法: INSTANT + INPLACE
-- ============================================================
-- 本文件由 generate_test_sql.py 自动生成, 请勿手动修改
-- 生成时间: 2026-09-20
-- ============================================================

SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET SESSION innodb_lock_wait_timeout = 50;

-- File 10: 特殊模式 (连续ALTER + 多列ALTER + 虚拟生成列)

-- Test Case: TC-SA0001
-- Consecutive ALTER: TINYINT UNSIGNED -> SMALLINT UNSIGNED -> MEDIUMINT UNSIGNED -> INT UNSIGNED -> BIGINT UNSIGNED
-- Algorithm: instant
DROP TABLE IF EXISTS t1_tc_sa0001, t2_tc_sa0001;
CREATE TABLE t1_tc_sa0001 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target TINYINT UNSIGNED,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_sa0001 (target) VALUES (0);
INSERT INTO t1_tc_sa0001 (target) VALUES (1);
INSERT INTO t1_tc_sa0001 (target) VALUES (255);
-- Step 1: ALTER to SMALLINT UNSIGNED
ALTER TABLE t1_tc_sa0001 MODIFY target SMALLINT UNSIGNED, ALGORITHM=instant;
INSERT INTO t1_tc_sa0001 (target) VALUES (256);
INSERT INTO t1_tc_sa0001 (target) VALUES (65535);
-- Step 2: ALTER to MEDIUMINT UNSIGNED
ALTER TABLE t1_tc_sa0001 MODIFY target MEDIUMINT UNSIGNED, ALGORITHM=instant;
INSERT INTO t1_tc_sa0001 (target) VALUES (65536);
INSERT INTO t1_tc_sa0001 (target) VALUES (16777215);
-- Step 3: ALTER to INT UNSIGNED
ALTER TABLE t1_tc_sa0001 MODIFY target INT UNSIGNED, ALGORITHM=instant;
INSERT INTO t1_tc_sa0001 (target) VALUES (16777216);
INSERT INTO t1_tc_sa0001 (target) VALUES (4294967295);
-- Step 4: ALTER to BIGINT UNSIGNED
ALTER TABLE t1_tc_sa0001 MODIFY target BIGINT UNSIGNED, ALGORITHM=instant;
INSERT INTO t1_tc_sa0001 (target) VALUES (4294967296);
INSERT INTO t1_tc_sa0001 (target) VALUES (18446744073709551615);
-- Oracle table with final type BIGINT UNSIGNED
CREATE TABLE t2_tc_sa0001 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target BIGINT UNSIGNED,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t2_tc_sa0001 (target) VALUES (0);
INSERT INTO t2_tc_sa0001 (target) VALUES (1);
INSERT INTO t2_tc_sa0001 (target) VALUES (255);
INSERT INTO t2_tc_sa0001 (target) VALUES (256);
INSERT INTO t2_tc_sa0001 (target) VALUES (65535);
INSERT INTO t2_tc_sa0001 (target) VALUES (65536);
INSERT INTO t2_tc_sa0001 (target) VALUES (16777215);
INSERT INTO t2_tc_sa0001 (target) VALUES (16777216);
INSERT INTO t2_tc_sa0001 (target) VALUES (4294967295);
INSERT INTO t2_tc_sa0001 (target) VALUES (4294967296);
INSERT INTO t2_tc_sa0001 (target) VALUES (18446744073709551615);
SELECT 'TC-SA0001' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_sa0001
   WHERE id NOT IN (SELECT id FROM t2_tc_sa0001)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_sa0001
   WHERE id NOT IN (SELECT id FROM t1_tc_sa0001)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_sa0001 a JOIN t2_tc_sa0001 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;

-- Test Case: TC-SA0002
-- Consecutive ALTER: TINYINT UNSIGNED -> SMALLINT UNSIGNED -> MEDIUMINT UNSIGNED -> INT UNSIGNED -> BIGINT UNSIGNED
-- Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_sa0002, t2_tc_sa0002;
CREATE TABLE t1_tc_sa0002 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target TINYINT UNSIGNED,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_sa0002 (target) VALUES (0);
INSERT INTO t1_tc_sa0002 (target) VALUES (1);
INSERT INTO t1_tc_sa0002 (target) VALUES (255);
-- Step 1: ALTER to SMALLINT UNSIGNED
ALTER TABLE t1_tc_sa0002 MODIFY target SMALLINT UNSIGNED, ALGORITHM=inplace;
INSERT INTO t1_tc_sa0002 (target) VALUES (256);
INSERT INTO t1_tc_sa0002 (target) VALUES (65535);
-- Step 2: ALTER to MEDIUMINT UNSIGNED
ALTER TABLE t1_tc_sa0002 MODIFY target MEDIUMINT UNSIGNED, ALGORITHM=inplace;
INSERT INTO t1_tc_sa0002 (target) VALUES (65536);
INSERT INTO t1_tc_sa0002 (target) VALUES (16777215);
-- Step 3: ALTER to INT UNSIGNED
ALTER TABLE t1_tc_sa0002 MODIFY target INT UNSIGNED, ALGORITHM=inplace;
INSERT INTO t1_tc_sa0002 (target) VALUES (16777216);
INSERT INTO t1_tc_sa0002 (target) VALUES (4294967295);
-- Step 4: ALTER to BIGINT UNSIGNED
ALTER TABLE t1_tc_sa0002 MODIFY target BIGINT UNSIGNED, ALGORITHM=inplace;
INSERT INTO t1_tc_sa0002 (target) VALUES (4294967296);
INSERT INTO t1_tc_sa0002 (target) VALUES (18446744073709551615);
-- Oracle table with final type BIGINT UNSIGNED
CREATE TABLE t2_tc_sa0002 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target BIGINT UNSIGNED,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t2_tc_sa0002 (target) VALUES (0);
INSERT INTO t2_tc_sa0002 (target) VALUES (1);
INSERT INTO t2_tc_sa0002 (target) VALUES (255);
INSERT INTO t2_tc_sa0002 (target) VALUES (256);
INSERT INTO t2_tc_sa0002 (target) VALUES (65535);
INSERT INTO t2_tc_sa0002 (target) VALUES (65536);
INSERT INTO t2_tc_sa0002 (target) VALUES (16777215);
INSERT INTO t2_tc_sa0002 (target) VALUES (16777216);
INSERT INTO t2_tc_sa0002 (target) VALUES (4294967295);
INSERT INTO t2_tc_sa0002 (target) VALUES (4294967296);
INSERT INTO t2_tc_sa0002 (target) VALUES (18446744073709551615);
SELECT 'TC-SA0002' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_sa0002
   WHERE id NOT IN (SELECT id FROM t2_tc_sa0002)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_sa0002
   WHERE id NOT IN (SELECT id FROM t1_tc_sa0002)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_sa0002 a JOIN t2_tc_sa0002 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;

-- Test Case: TC-SA0003
-- Consecutive ALTER: TINYINT -> SMALLINT -> MEDIUMINT -> INT -> BIGINT
-- Algorithm: instant
DROP TABLE IF EXISTS t1_tc_sa0003, t2_tc_sa0003;
CREATE TABLE t1_tc_sa0003 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target TINYINT,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_sa0003 (target) VALUES (-128);
INSERT INTO t1_tc_sa0003 (target) VALUES (0);
INSERT INTO t1_tc_sa0003 (target) VALUES (1);
INSERT INTO t1_tc_sa0003 (target) VALUES (127);
-- Step 1: ALTER to SMALLINT
ALTER TABLE t1_tc_sa0003 MODIFY target SMALLINT, ALGORITHM=instant;
INSERT INTO t1_tc_sa0003 (target) VALUES (128);
INSERT INTO t1_tc_sa0003 (target) VALUES (32767);
-- Step 2: ALTER to MEDIUMINT
ALTER TABLE t1_tc_sa0003 MODIFY target MEDIUMINT, ALGORITHM=instant;
INSERT INTO t1_tc_sa0003 (target) VALUES (32768);
INSERT INTO t1_tc_sa0003 (target) VALUES (8388607);
-- Step 3: ALTER to INT
ALTER TABLE t1_tc_sa0003 MODIFY target INT, ALGORITHM=instant;
INSERT INTO t1_tc_sa0003 (target) VALUES (8388608);
INSERT INTO t1_tc_sa0003 (target) VALUES (2147483647);
-- Step 4: ALTER to BIGINT
ALTER TABLE t1_tc_sa0003 MODIFY target BIGINT, ALGORITHM=instant;
INSERT INTO t1_tc_sa0003 (target) VALUES (2147483648);
INSERT INTO t1_tc_sa0003 (target) VALUES (9223372036854775807);
-- Oracle table with final type BIGINT
CREATE TABLE t2_tc_sa0003 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target BIGINT,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t2_tc_sa0003 (target) VALUES (-128);
INSERT INTO t2_tc_sa0003 (target) VALUES (0);
INSERT INTO t2_tc_sa0003 (target) VALUES (1);
INSERT INTO t2_tc_sa0003 (target) VALUES (127);
INSERT INTO t2_tc_sa0003 (target) VALUES (128);
INSERT INTO t2_tc_sa0003 (target) VALUES (32767);
INSERT INTO t2_tc_sa0003 (target) VALUES (32768);
INSERT INTO t2_tc_sa0003 (target) VALUES (8388607);
INSERT INTO t2_tc_sa0003 (target) VALUES (8388608);
INSERT INTO t2_tc_sa0003 (target) VALUES (2147483647);
INSERT INTO t2_tc_sa0003 (target) VALUES (2147483648);
INSERT INTO t2_tc_sa0003 (target) VALUES (9223372036854775807);
SELECT 'TC-SA0003' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_sa0003
   WHERE id NOT IN (SELECT id FROM t2_tc_sa0003)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_sa0003
   WHERE id NOT IN (SELECT id FROM t1_tc_sa0003)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_sa0003 a JOIN t2_tc_sa0003 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;

-- Test Case: TC-SA0004
-- Consecutive ALTER: TINYINT -> SMALLINT -> MEDIUMINT -> INT -> BIGINT
-- Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_sa0004, t2_tc_sa0004;
CREATE TABLE t1_tc_sa0004 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target TINYINT,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_sa0004 (target) VALUES (-128);
INSERT INTO t1_tc_sa0004 (target) VALUES (0);
INSERT INTO t1_tc_sa0004 (target) VALUES (1);
INSERT INTO t1_tc_sa0004 (target) VALUES (127);
-- Step 1: ALTER to SMALLINT
ALTER TABLE t1_tc_sa0004 MODIFY target SMALLINT, ALGORITHM=inplace;
INSERT INTO t1_tc_sa0004 (target) VALUES (128);
INSERT INTO t1_tc_sa0004 (target) VALUES (32767);
-- Step 2: ALTER to MEDIUMINT
ALTER TABLE t1_tc_sa0004 MODIFY target MEDIUMINT, ALGORITHM=inplace;
INSERT INTO t1_tc_sa0004 (target) VALUES (32768);
INSERT INTO t1_tc_sa0004 (target) VALUES (8388607);
-- Step 3: ALTER to INT
ALTER TABLE t1_tc_sa0004 MODIFY target INT, ALGORITHM=inplace;
INSERT INTO t1_tc_sa0004 (target) VALUES (8388608);
INSERT INTO t1_tc_sa0004 (target) VALUES (2147483647);
-- Step 4: ALTER to BIGINT
ALTER TABLE t1_tc_sa0004 MODIFY target BIGINT, ALGORITHM=inplace;
INSERT INTO t1_tc_sa0004 (target) VALUES (2147483648);
INSERT INTO t1_tc_sa0004 (target) VALUES (9223372036854775807);
-- Oracle table with final type BIGINT
CREATE TABLE t2_tc_sa0004 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target BIGINT,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t2_tc_sa0004 (target) VALUES (-128);
INSERT INTO t2_tc_sa0004 (target) VALUES (0);
INSERT INTO t2_tc_sa0004 (target) VALUES (1);
INSERT INTO t2_tc_sa0004 (target) VALUES (127);
INSERT INTO t2_tc_sa0004 (target) VALUES (128);
INSERT INTO t2_tc_sa0004 (target) VALUES (32767);
INSERT INTO t2_tc_sa0004 (target) VALUES (32768);
INSERT INTO t2_tc_sa0004 (target) VALUES (8388607);
INSERT INTO t2_tc_sa0004 (target) VALUES (8388608);
INSERT INTO t2_tc_sa0004 (target) VALUES (2147483647);
INSERT INTO t2_tc_sa0004 (target) VALUES (2147483648);
INSERT INTO t2_tc_sa0004 (target) VALUES (9223372036854775807);
SELECT 'TC-SA0004' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_sa0004
   WHERE id NOT IN (SELECT id FROM t2_tc_sa0004)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_sa0004
   WHERE id NOT IN (SELECT id FROM t1_tc_sa0004)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_sa0004 a JOIN t2_tc_sa0004 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;

-- Test Case: TC-SA0005
-- Multi-column ALTER, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_sa0005, t2_tc_sa0005;
CREATE TABLE t1_tc_sa0005 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  col_int INT,
  col_char CHAR(10) CHARACTER SET utf8mb4,
  col_varchar VARCHAR(50) CHARACTER SET utf8mb4
) ENGINE=InnoDB;
INSERT INTO t1_tc_sa0005 (col_int, col_char, col_varchar)
VALUES (42, 'hello', 'world');
ALTER TABLE t1_tc_sa0005 MODIFY col_int BIGINT, MODIFY col_char CHAR(20) CHARACTER SET utf8mb4, MODIFY col_varchar VARCHAR(100) CHARACTER SET utf8mb4, ALGORITHM=instant;
INSERT INTO t1_tc_sa0005 (col_int, col_char, col_varchar)
VALUES (2147483648, 'hello_world_long', 'extended_string');
CREATE TABLE t2_tc_sa0005 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  col_int BIGINT,
  col_char CHAR(20) CHARACTER SET utf8mb4,
  col_varchar VARCHAR(100) CHARACTER SET utf8mb4
) ENGINE=InnoDB;
INSERT INTO t2_tc_sa0005 (col_int, col_char, col_varchar)
VALUES (42, 'hello', 'world');
INSERT INTO t2_tc_sa0005 (col_int, col_char, col_varchar)
VALUES (2147483648, 'hello_world_long', 'extended_string');
SELECT 'TC-SA0005' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_sa0005
   WHERE id NOT IN (SELECT id FROM t2_tc_sa0005)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_sa0005
   WHERE id NOT IN (SELECT id FROM t1_tc_sa0005)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_sa0005 a JOIN t2_tc_sa0005 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.col_int <=> b.col_int AND a.col_char <=> b.col_char AND a.col_varchar <=> b.col_varchar)
) AS mismatches;

-- Test Case: TC-SA0006
-- Multi-column ALTER, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_sa0006, t2_tc_sa0006;
CREATE TABLE t1_tc_sa0006 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  col_int INT,
  col_char CHAR(10) CHARACTER SET utf8mb4,
  col_varchar VARCHAR(50) CHARACTER SET utf8mb4
) ENGINE=InnoDB;
INSERT INTO t1_tc_sa0006 (col_int, col_char, col_varchar)
VALUES (42, 'hello', 'world');
ALTER TABLE t1_tc_sa0006 MODIFY col_int BIGINT, MODIFY col_char CHAR(20) CHARACTER SET utf8mb4, MODIFY col_varchar VARCHAR(100) CHARACTER SET utf8mb4, ALGORITHM=inplace;
INSERT INTO t1_tc_sa0006 (col_int, col_char, col_varchar)
VALUES (2147483648, 'hello_world_long', 'extended_string');
CREATE TABLE t2_tc_sa0006 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  col_int BIGINT,
  col_char CHAR(20) CHARACTER SET utf8mb4,
  col_varchar VARCHAR(100) CHARACTER SET utf8mb4
) ENGINE=InnoDB;
INSERT INTO t2_tc_sa0006 (col_int, col_char, col_varchar)
VALUES (42, 'hello', 'world');
INSERT INTO t2_tc_sa0006 (col_int, col_char, col_varchar)
VALUES (2147483648, 'hello_world_long', 'extended_string');
SELECT 'TC-SA0006' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_sa0006
   WHERE id NOT IN (SELECT id FROM t2_tc_sa0006)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_sa0006
   WHERE id NOT IN (SELECT id FROM t1_tc_sa0006)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_sa0006 a JOIN t2_tc_sa0006 b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.col_int <=> b.col_int AND a.col_char <=> b.col_char AND a.col_varchar <=> b.col_varchar)
) AS mismatches;

-- Test Case: TC-SA0007
-- Virtual generated column + function index, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_sa0007, t2_tc_sa0007;
CREATE TABLE t1_tc_sa0007 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  base_col INT,
  vcol BIGINT AS (base_col * 2) VIRTUAL,
  INDEX idx_vcol (vcol)
) ENGINE=InnoDB;
INSERT INTO t1_tc_sa0007 (base_col) VALUES (0), (1), (-1), (2147483647), (42), (-42), (NULL);
-- ALTER base_col INT -> BIGINT, expected: FAIL
ALTER TABLE t1_tc_sa0007 MODIFY base_col BIGINT, ALGORITHM=instant;
CREATE TABLE t2_tc_sa0007 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  base_col INT,
  vcol BIGINT AS (base_col * 2) VIRTUAL
) ENGINE=InnoDB;
INSERT INTO t2_tc_sa0007 (base_col) VALUES (0), (1), (-1), (2147483647), (42), (-42), (NULL);
SELECT 'TC-SA0007' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_sa0007
   WHERE id NOT IN (SELECT id FROM t2_tc_sa0007)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_sa0007
   WHERE id NOT IN (SELECT id FROM t1_tc_sa0007)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_sa0007 a JOIN t2_tc_sa0007 b ON a.id = b.id
   WHERE NOT (a.base_col <=> b.base_col)
) AS mismatches;

-- Test Case: TC-SA0008
-- Virtual generated column + function index, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_sa0008, t2_tc_sa0008;
CREATE TABLE t1_tc_sa0008 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  base_col INT,
  vcol BIGINT AS (base_col * 2) VIRTUAL,
  INDEX idx_vcol (vcol)
) ENGINE=InnoDB;
INSERT INTO t1_tc_sa0008 (base_col) VALUES (0), (1), (-1), (2147483647), (42), (-42), (NULL);
-- ALTER base_col INT -> BIGINT, expected: SUCCESS
ALTER TABLE t1_tc_sa0008 MODIFY base_col BIGINT, ALGORITHM=inplace;
INSERT INTO t1_tc_sa0008 (base_col) VALUES (2147483648), (9223372036854775807), (-9223372036854775808);
CREATE TABLE t2_tc_sa0008 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  base_col BIGINT,
  vcol BIGINT AS (base_col * 2) VIRTUAL
) ENGINE=InnoDB;
INSERT INTO t2_tc_sa0008 (base_col) VALUES (0), (1), (-1), (2147483647), (42), (-42), (NULL);
INSERT INTO t2_tc_sa0008 (base_col) VALUES (2147483648), (9223372036854775807), (-9223372036854775808);
SELECT 'TC-SA0008' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_sa0008
   WHERE id NOT IN (SELECT id FROM t2_tc_sa0008)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_sa0008
   WHERE id NOT IN (SELECT id FROM t1_tc_sa0008)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_sa0008 a JOIN t2_tc_sa0008 b ON a.id = b.id
   WHERE NOT (a.base_col <=> b.base_col)
) AS mismatches;

