-- ============================================================
-- RDS MySQL DDL 秒级/在线修改列类型 测试套件 — 阿里云环境
-- 环境说明: 所有功能开关默认开启
-- 覆盖类型: 整数(SIGNED/UNSIGNED) + CHAR + VARCHAR
-- 覆盖算法: INSTANT + INPLACE
-- ============================================================
-- 本文件由 generate_test_sql.py 自动生成, 请勿手动修改
-- Suite-Revision: 505d13b7cf36   (生成器源码哈希; 时间戳见 results/generation_manifest.json)
-- 用例 ID 规则: TC-<文件号>-<作用域>-<序号>-<IT|IP>  —— 全局唯一
--   作用域 REG=普通表 OFAT/二元组, ATR=列属性保持, SPE=特殊模式,
--          FK=外键, PTK=分区(目标列是分区键), PNK=分区(目标列非分区键)
-- ============================================================

SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET SESSION innodb_lock_wait_timeout = 50;

-- File 11: 外键表测试

-- Test Case: TC-11-FK-0001-IT
-- FK Scenario: child, Algorithm: instant
-- Type: INT -> BIGINT
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0001_it, tp_tc_11_fk_0001_it, t2_tc_11_fk_0001_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0001_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0001_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0001_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0001_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0001_it (fk_col) VALUES (0);
INSERT INTO tc_tc_11_fk_0001_it (fk_col) VALUES (0);
INSERT INTO tp_tc_11_fk_0001_it (fk_col) VALUES (1);
INSERT INTO tc_tc_11_fk_0001_it (fk_col) VALUES (1);
INSERT INTO tp_tc_11_fk_0001_it (fk_col) VALUES (-1);
INSERT INTO tc_tc_11_fk_0001_it (fk_col) VALUES (-1);
INSERT INTO tp_tc_11_fk_0001_it (fk_col) VALUES (42);
INSERT INTO tc_tc_11_fk_0001_it (fk_col) VALUES (42);
INSERT INTO tp_tc_11_fk_0001_it (fk_col) VALUES (127);
INSERT INTO tc_tc_11_fk_0001_it (fk_col) VALUES (127);
-- ALTER child table only
ALTER TABLE tc_tc_11_fk_0001_it MODIFY fk_col BIGINT, ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0001_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col INT, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0001_it (fk_col) VALUES (0);
INSERT INTO t2_tc_11_fk_0001_it (fk_col) VALUES (1);
INSERT INTO t2_tc_11_fk_0001_it (fk_col) VALUES (-1);
INSERT INTO t2_tc_11_fk_0001_it (fk_col) VALUES (42);
INSERT INTO t2_tc_11_fk_0001_it (fk_col) VALUES (127);
SELECT 'TC-11-FK-0001-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0001_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0001_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0001_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0001_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0001_it a JOIN t2_tc_11_fk_0001_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-11-FK-0002-IT
-- FK Scenario: parent, Algorithm: instant
-- Type: INT -> BIGINT
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0002_it, tp_tc_11_fk_0002_it, t2_tc_11_fk_0002_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0002_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0002_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0002_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0002_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0002_it (fk_col) VALUES (0);
INSERT INTO tc_tc_11_fk_0002_it (fk_col) VALUES (0);
INSERT INTO tp_tc_11_fk_0002_it (fk_col) VALUES (1);
INSERT INTO tc_tc_11_fk_0002_it (fk_col) VALUES (1);
INSERT INTO tp_tc_11_fk_0002_it (fk_col) VALUES (-1);
INSERT INTO tc_tc_11_fk_0002_it (fk_col) VALUES (-1);
INSERT INTO tp_tc_11_fk_0002_it (fk_col) VALUES (42);
INSERT INTO tc_tc_11_fk_0002_it (fk_col) VALUES (42);
INSERT INTO tp_tc_11_fk_0002_it (fk_col) VALUES (127);
INSERT INTO tc_tc_11_fk_0002_it (fk_col) VALUES (127);
-- ALTER parent table only
ALTER TABLE tp_tc_11_fk_0002_it MODIFY fk_col BIGINT, ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0002_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col INT, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0002_it (fk_col) VALUES (0);
INSERT INTO t2_tc_11_fk_0002_it (fk_col) VALUES (1);
INSERT INTO t2_tc_11_fk_0002_it (fk_col) VALUES (-1);
INSERT INTO t2_tc_11_fk_0002_it (fk_col) VALUES (42);
INSERT INTO t2_tc_11_fk_0002_it (fk_col) VALUES (127);
SELECT 'TC-11-FK-0002-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0002_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0002_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0002_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0002_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0002_it a JOIN t2_tc_11_fk_0002_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-11-FK-0003-IT
-- FK Scenario: both, Algorithm: instant
-- Type: INT -> BIGINT
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0003_it, tp_tc_11_fk_0003_it, t2_tc_11_fk_0003_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0003_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0003_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0003_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0003_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0003_it (fk_col) VALUES (0);
INSERT INTO tc_tc_11_fk_0003_it (fk_col) VALUES (0);
INSERT INTO tp_tc_11_fk_0003_it (fk_col) VALUES (1);
INSERT INTO tc_tc_11_fk_0003_it (fk_col) VALUES (1);
INSERT INTO tp_tc_11_fk_0003_it (fk_col) VALUES (-1);
INSERT INTO tc_tc_11_fk_0003_it (fk_col) VALUES (-1);
INSERT INTO tp_tc_11_fk_0003_it (fk_col) VALUES (42);
INSERT INTO tc_tc_11_fk_0003_it (fk_col) VALUES (42);
INSERT INTO tp_tc_11_fk_0003_it (fk_col) VALUES (127);
INSERT INTO tc_tc_11_fk_0003_it (fk_col) VALUES (127);
-- ALTER both tables (parent first, then child)
ALTER TABLE tp_tc_11_fk_0003_it MODIFY fk_col BIGINT, ALGORITHM=instant;
ALTER TABLE tc_tc_11_fk_0003_it MODIFY fk_col BIGINT, ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0003_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col INT, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0003_it (fk_col) VALUES (0);
INSERT INTO t2_tc_11_fk_0003_it (fk_col) VALUES (1);
INSERT INTO t2_tc_11_fk_0003_it (fk_col) VALUES (-1);
INSERT INTO t2_tc_11_fk_0003_it (fk_col) VALUES (42);
INSERT INTO t2_tc_11_fk_0003_it (fk_col) VALUES (127);
SELECT 'TC-11-FK-0003-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0003_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0003_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0003_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0003_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0003_it a JOIN t2_tc_11_fk_0003_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-11-FK-0004-IT
-- FK Scenario: non_fk, Algorithm: instant
-- Type: INT -> BIGINT
-- Expected: SUCCESS
-- Expected ALTER: SUCCESS
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0004_it, tp_tc_11_fk_0004_it, t2_tc_11_fk_0004_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0004_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0004_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0004_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0004_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0004_it (fk_col) VALUES (0);
INSERT INTO tc_tc_11_fk_0004_it (fk_col) VALUES (0);
INSERT INTO tp_tc_11_fk_0004_it (fk_col) VALUES (1);
INSERT INTO tc_tc_11_fk_0004_it (fk_col) VALUES (1);
INSERT INTO tp_tc_11_fk_0004_it (fk_col) VALUES (-1);
INSERT INTO tc_tc_11_fk_0004_it (fk_col) VALUES (-1);
INSERT INTO tp_tc_11_fk_0004_it (fk_col) VALUES (42);
INSERT INTO tc_tc_11_fk_0004_it (fk_col) VALUES (42);
INSERT INTO tp_tc_11_fk_0004_it (fk_col) VALUES (127);
INSERT INTO tc_tc_11_fk_0004_it (fk_col) VALUES (127);
-- ALTER non-FK column (data column)
ALTER TABLE tc_tc_11_fk_0004_it MODIFY data VARCHAR(50) DEFAULT 'child', ALGORITHM=instant;
INSERT INTO tp_tc_11_fk_0004_it (fk_col) VALUES (128);
INSERT INTO tc_tc_11_fk_0004_it (fk_col) VALUES (128);
INSERT INTO tp_tc_11_fk_0004_it (fk_col) VALUES (255);
INSERT INTO tc_tc_11_fk_0004_it (fk_col) VALUES (255);
INSERT INTO tp_tc_11_fk_0004_it (fk_col) VALUES (1000);
INSERT INTO tc_tc_11_fk_0004_it (fk_col) VALUES (1000);
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0004_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col INT, data VARCHAR(50) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0004_it (fk_col) VALUES (0);
INSERT INTO t2_tc_11_fk_0004_it (fk_col) VALUES (1);
INSERT INTO t2_tc_11_fk_0004_it (fk_col) VALUES (-1);
INSERT INTO t2_tc_11_fk_0004_it (fk_col) VALUES (42);
INSERT INTO t2_tc_11_fk_0004_it (fk_col) VALUES (127);
INSERT INTO t2_tc_11_fk_0004_it (fk_col) VALUES (128);
INSERT INTO t2_tc_11_fk_0004_it (fk_col) VALUES (255);
INSERT INTO t2_tc_11_fk_0004_it (fk_col) VALUES (1000);
SELECT 'TC-11-FK-0004-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0004_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0004_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0004_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0004_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0004_it a JOIN t2_tc_11_fk_0004_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-11-FK-0005-IP
-- FK Scenario: child, Algorithm: inplace
-- Type: INT -> BIGINT
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0005_ip, tp_tc_11_fk_0005_ip, t2_tc_11_fk_0005_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0005_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0005_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0005_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0005_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0005_ip (fk_col) VALUES (0);
INSERT INTO tc_tc_11_fk_0005_ip (fk_col) VALUES (0);
INSERT INTO tp_tc_11_fk_0005_ip (fk_col) VALUES (1);
INSERT INTO tc_tc_11_fk_0005_ip (fk_col) VALUES (1);
INSERT INTO tp_tc_11_fk_0005_ip (fk_col) VALUES (-1);
INSERT INTO tc_tc_11_fk_0005_ip (fk_col) VALUES (-1);
INSERT INTO tp_tc_11_fk_0005_ip (fk_col) VALUES (42);
INSERT INTO tc_tc_11_fk_0005_ip (fk_col) VALUES (42);
INSERT INTO tp_tc_11_fk_0005_ip (fk_col) VALUES (127);
INSERT INTO tc_tc_11_fk_0005_ip (fk_col) VALUES (127);
-- ALTER child table only
ALTER TABLE tc_tc_11_fk_0005_ip MODIFY fk_col BIGINT, ALGORITHM=inplace;
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0005_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col INT, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0005_ip (fk_col) VALUES (0);
INSERT INTO t2_tc_11_fk_0005_ip (fk_col) VALUES (1);
INSERT INTO t2_tc_11_fk_0005_ip (fk_col) VALUES (-1);
INSERT INTO t2_tc_11_fk_0005_ip (fk_col) VALUES (42);
INSERT INTO t2_tc_11_fk_0005_ip (fk_col) VALUES (127);
SELECT 'TC-11-FK-0005-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0005_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0005_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0005_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0005_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0005_ip a JOIN t2_tc_11_fk_0005_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-11-FK-0006-IP
-- FK Scenario: parent, Algorithm: inplace
-- Type: INT -> BIGINT
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0006_ip, tp_tc_11_fk_0006_ip, t2_tc_11_fk_0006_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0006_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0006_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0006_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0006_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0006_ip (fk_col) VALUES (0);
INSERT INTO tc_tc_11_fk_0006_ip (fk_col) VALUES (0);
INSERT INTO tp_tc_11_fk_0006_ip (fk_col) VALUES (1);
INSERT INTO tc_tc_11_fk_0006_ip (fk_col) VALUES (1);
INSERT INTO tp_tc_11_fk_0006_ip (fk_col) VALUES (-1);
INSERT INTO tc_tc_11_fk_0006_ip (fk_col) VALUES (-1);
INSERT INTO tp_tc_11_fk_0006_ip (fk_col) VALUES (42);
INSERT INTO tc_tc_11_fk_0006_ip (fk_col) VALUES (42);
INSERT INTO tp_tc_11_fk_0006_ip (fk_col) VALUES (127);
INSERT INTO tc_tc_11_fk_0006_ip (fk_col) VALUES (127);
-- ALTER parent table only
ALTER TABLE tp_tc_11_fk_0006_ip MODIFY fk_col BIGINT, ALGORITHM=inplace;
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0006_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col INT, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0006_ip (fk_col) VALUES (0);
INSERT INTO t2_tc_11_fk_0006_ip (fk_col) VALUES (1);
INSERT INTO t2_tc_11_fk_0006_ip (fk_col) VALUES (-1);
INSERT INTO t2_tc_11_fk_0006_ip (fk_col) VALUES (42);
INSERT INTO t2_tc_11_fk_0006_ip (fk_col) VALUES (127);
SELECT 'TC-11-FK-0006-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0006_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0006_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0006_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0006_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0006_ip a JOIN t2_tc_11_fk_0006_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-11-FK-0007-IP
-- FK Scenario: both, Algorithm: inplace
-- Type: INT -> BIGINT
-- Expected: SUCCESS
-- Expected ALTER: SUCCESS
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0007_ip, tp_tc_11_fk_0007_ip, t2_tc_11_fk_0007_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0007_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0007_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0007_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0007_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0007_ip (fk_col) VALUES (0);
INSERT INTO tc_tc_11_fk_0007_ip (fk_col) VALUES (0);
INSERT INTO tp_tc_11_fk_0007_ip (fk_col) VALUES (1);
INSERT INTO tc_tc_11_fk_0007_ip (fk_col) VALUES (1);
INSERT INTO tp_tc_11_fk_0007_ip (fk_col) VALUES (-1);
INSERT INTO tc_tc_11_fk_0007_ip (fk_col) VALUES (-1);
INSERT INTO tp_tc_11_fk_0007_ip (fk_col) VALUES (42);
INSERT INTO tc_tc_11_fk_0007_ip (fk_col) VALUES (42);
INSERT INTO tp_tc_11_fk_0007_ip (fk_col) VALUES (127);
INSERT INTO tc_tc_11_fk_0007_ip (fk_col) VALUES (127);
-- ALTER both tables (parent first, then child)
ALTER TABLE tp_tc_11_fk_0007_ip MODIFY fk_col BIGINT, ALGORITHM=inplace;
ALTER TABLE tc_tc_11_fk_0007_ip MODIFY fk_col BIGINT, ALGORITHM=inplace;
INSERT INTO tp_tc_11_fk_0007_ip (fk_col) VALUES (128);
INSERT INTO tc_tc_11_fk_0007_ip (fk_col) VALUES (128);
INSERT INTO tp_tc_11_fk_0007_ip (fk_col) VALUES (255);
INSERT INTO tc_tc_11_fk_0007_ip (fk_col) VALUES (255);
INSERT INTO tp_tc_11_fk_0007_ip (fk_col) VALUES (1000);
INSERT INTO tc_tc_11_fk_0007_ip (fk_col) VALUES (1000);
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0007_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col BIGINT, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0007_ip (fk_col) VALUES (0);
INSERT INTO t2_tc_11_fk_0007_ip (fk_col) VALUES (1);
INSERT INTO t2_tc_11_fk_0007_ip (fk_col) VALUES (-1);
INSERT INTO t2_tc_11_fk_0007_ip (fk_col) VALUES (42);
INSERT INTO t2_tc_11_fk_0007_ip (fk_col) VALUES (127);
INSERT INTO t2_tc_11_fk_0007_ip (fk_col) VALUES (128);
INSERT INTO t2_tc_11_fk_0007_ip (fk_col) VALUES (255);
INSERT INTO t2_tc_11_fk_0007_ip (fk_col) VALUES (1000);
SELECT 'TC-11-FK-0007-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0007_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0007_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0007_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0007_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0007_ip a JOIN t2_tc_11_fk_0007_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-11-FK-0008-IP
-- FK Scenario: non_fk, Algorithm: inplace
-- Type: INT -> BIGINT
-- Expected: SUCCESS
-- Expected ALTER: SUCCESS
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0008_ip, tp_tc_11_fk_0008_ip, t2_tc_11_fk_0008_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0008_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0008_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col INT,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0008_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0008_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0008_ip (fk_col) VALUES (0);
INSERT INTO tc_tc_11_fk_0008_ip (fk_col) VALUES (0);
INSERT INTO tp_tc_11_fk_0008_ip (fk_col) VALUES (1);
INSERT INTO tc_tc_11_fk_0008_ip (fk_col) VALUES (1);
INSERT INTO tp_tc_11_fk_0008_ip (fk_col) VALUES (-1);
INSERT INTO tc_tc_11_fk_0008_ip (fk_col) VALUES (-1);
INSERT INTO tp_tc_11_fk_0008_ip (fk_col) VALUES (42);
INSERT INTO tc_tc_11_fk_0008_ip (fk_col) VALUES (42);
INSERT INTO tp_tc_11_fk_0008_ip (fk_col) VALUES (127);
INSERT INTO tc_tc_11_fk_0008_ip (fk_col) VALUES (127);
-- ALTER non-FK column (data column)
ALTER TABLE tc_tc_11_fk_0008_ip MODIFY data VARCHAR(50) DEFAULT 'child', ALGORITHM=inplace;
INSERT INTO tp_tc_11_fk_0008_ip (fk_col) VALUES (128);
INSERT INTO tc_tc_11_fk_0008_ip (fk_col) VALUES (128);
INSERT INTO tp_tc_11_fk_0008_ip (fk_col) VALUES (255);
INSERT INTO tc_tc_11_fk_0008_ip (fk_col) VALUES (255);
INSERT INTO tp_tc_11_fk_0008_ip (fk_col) VALUES (1000);
INSERT INTO tc_tc_11_fk_0008_ip (fk_col) VALUES (1000);
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0008_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col INT, data VARCHAR(50) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0008_ip (fk_col) VALUES (0);
INSERT INTO t2_tc_11_fk_0008_ip (fk_col) VALUES (1);
INSERT INTO t2_tc_11_fk_0008_ip (fk_col) VALUES (-1);
INSERT INTO t2_tc_11_fk_0008_ip (fk_col) VALUES (42);
INSERT INTO t2_tc_11_fk_0008_ip (fk_col) VALUES (127);
INSERT INTO t2_tc_11_fk_0008_ip (fk_col) VALUES (128);
INSERT INTO t2_tc_11_fk_0008_ip (fk_col) VALUES (255);
INSERT INTO t2_tc_11_fk_0008_ip (fk_col) VALUES (1000);
SELECT 'TC-11-FK-0008-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0008_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0008_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0008_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0008_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0008_ip a JOIN t2_tc_11_fk_0008_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-11-FK-0009-IT
-- FK Scenario: child, Algorithm: instant
-- Type: VARCHAR(50) -> VARCHAR(100)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0009_it, tp_tc_11_fk_0009_it, t2_tc_11_fk_0009_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0009_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0009_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0009_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0009_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0009_it (fk_col) VALUES ('hello');
INSERT INTO tc_tc_11_fk_0009_it (fk_col) VALUES ('hello');
INSERT INTO tp_tc_11_fk_0009_it (fk_col) VALUES ('world');
INSERT INTO tc_tc_11_fk_0009_it (fk_col) VALUES ('world');
INSERT INTO tp_tc_11_fk_0009_it (fk_col) VALUES ('test');
INSERT INTO tc_tc_11_fk_0009_it (fk_col) VALUES ('test');
INSERT INTO tp_tc_11_fk_0009_it (fk_col) VALUES ('abc');
INSERT INTO tc_tc_11_fk_0009_it (fk_col) VALUES ('abc');
-- ALTER child table only
ALTER TABLE tc_tc_11_fk_0009_it MODIFY fk_col VARCHAR(100) CHARACTER SET latin1, ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0009_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARCHAR(50) CHARACTER SET latin1, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0009_it (fk_col) VALUES ('hello');
INSERT INTO t2_tc_11_fk_0009_it (fk_col) VALUES ('world');
INSERT INTO t2_tc_11_fk_0009_it (fk_col) VALUES ('test');
INSERT INTO t2_tc_11_fk_0009_it (fk_col) VALUES ('abc');
SELECT 'TC-11-FK-0009-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0009_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0009_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0009_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0009_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0009_it a JOIN t2_tc_11_fk_0009_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-11-FK-0010-IT
-- FK Scenario: parent, Algorithm: instant
-- Type: VARCHAR(50) -> VARCHAR(100)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0010_it, tp_tc_11_fk_0010_it, t2_tc_11_fk_0010_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0010_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0010_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0010_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0010_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0010_it (fk_col) VALUES ('hello');
INSERT INTO tc_tc_11_fk_0010_it (fk_col) VALUES ('hello');
INSERT INTO tp_tc_11_fk_0010_it (fk_col) VALUES ('world');
INSERT INTO tc_tc_11_fk_0010_it (fk_col) VALUES ('world');
INSERT INTO tp_tc_11_fk_0010_it (fk_col) VALUES ('test');
INSERT INTO tc_tc_11_fk_0010_it (fk_col) VALUES ('test');
INSERT INTO tp_tc_11_fk_0010_it (fk_col) VALUES ('abc');
INSERT INTO tc_tc_11_fk_0010_it (fk_col) VALUES ('abc');
-- ALTER parent table only
ALTER TABLE tp_tc_11_fk_0010_it MODIFY fk_col VARCHAR(100) CHARACTER SET latin1, ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0010_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARCHAR(50) CHARACTER SET latin1, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0010_it (fk_col) VALUES ('hello');
INSERT INTO t2_tc_11_fk_0010_it (fk_col) VALUES ('world');
INSERT INTO t2_tc_11_fk_0010_it (fk_col) VALUES ('test');
INSERT INTO t2_tc_11_fk_0010_it (fk_col) VALUES ('abc');
SELECT 'TC-11-FK-0010-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0010_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0010_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0010_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0010_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0010_it a JOIN t2_tc_11_fk_0010_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-11-FK-0011-IT
-- FK Scenario: both, Algorithm: instant
-- Type: VARCHAR(50) -> VARCHAR(100)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0011_it, tp_tc_11_fk_0011_it, t2_tc_11_fk_0011_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0011_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0011_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0011_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0011_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0011_it (fk_col) VALUES ('hello');
INSERT INTO tc_tc_11_fk_0011_it (fk_col) VALUES ('hello');
INSERT INTO tp_tc_11_fk_0011_it (fk_col) VALUES ('world');
INSERT INTO tc_tc_11_fk_0011_it (fk_col) VALUES ('world');
INSERT INTO tp_tc_11_fk_0011_it (fk_col) VALUES ('test');
INSERT INTO tc_tc_11_fk_0011_it (fk_col) VALUES ('test');
INSERT INTO tp_tc_11_fk_0011_it (fk_col) VALUES ('abc');
INSERT INTO tc_tc_11_fk_0011_it (fk_col) VALUES ('abc');
-- ALTER both tables (parent first, then child)
ALTER TABLE tp_tc_11_fk_0011_it MODIFY fk_col VARCHAR(100) CHARACTER SET latin1, ALGORITHM=instant;
ALTER TABLE tc_tc_11_fk_0011_it MODIFY fk_col VARCHAR(100) CHARACTER SET latin1, ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0011_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARCHAR(50) CHARACTER SET latin1, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0011_it (fk_col) VALUES ('hello');
INSERT INTO t2_tc_11_fk_0011_it (fk_col) VALUES ('world');
INSERT INTO t2_tc_11_fk_0011_it (fk_col) VALUES ('test');
INSERT INTO t2_tc_11_fk_0011_it (fk_col) VALUES ('abc');
SELECT 'TC-11-FK-0011-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0011_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0011_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0011_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0011_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0011_it a JOIN t2_tc_11_fk_0011_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-11-FK-0012-IT
-- FK Scenario: non_fk, Algorithm: instant
-- Type: VARCHAR(50) -> VARCHAR(100)
-- Expected: SUCCESS
-- Expected ALTER: SUCCESS
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0012_it, tp_tc_11_fk_0012_it, t2_tc_11_fk_0012_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0012_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0012_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0012_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0012_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0012_it (fk_col) VALUES ('hello');
INSERT INTO tc_tc_11_fk_0012_it (fk_col) VALUES ('hello');
INSERT INTO tp_tc_11_fk_0012_it (fk_col) VALUES ('world');
INSERT INTO tc_tc_11_fk_0012_it (fk_col) VALUES ('world');
INSERT INTO tp_tc_11_fk_0012_it (fk_col) VALUES ('test');
INSERT INTO tc_tc_11_fk_0012_it (fk_col) VALUES ('test');
INSERT INTO tp_tc_11_fk_0012_it (fk_col) VALUES ('abc');
INSERT INTO tc_tc_11_fk_0012_it (fk_col) VALUES ('abc');
-- ALTER non-FK column (data column)
ALTER TABLE tc_tc_11_fk_0012_it MODIFY data VARCHAR(50) DEFAULT 'child', ALGORITHM=instant;
INSERT INTO tp_tc_11_fk_0012_it (fk_col) VALUES ('hello_world');
INSERT INTO tc_tc_11_fk_0012_it (fk_col) VALUES ('hello_world');
INSERT INTO tp_tc_11_fk_0012_it (fk_col) VALUES ('a');
INSERT INTO tc_tc_11_fk_0012_it (fk_col) VALUES ('a');
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0012_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARCHAR(50) CHARACTER SET latin1, data VARCHAR(50) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0012_it (fk_col) VALUES ('hello');
INSERT INTO t2_tc_11_fk_0012_it (fk_col) VALUES ('world');
INSERT INTO t2_tc_11_fk_0012_it (fk_col) VALUES ('test');
INSERT INTO t2_tc_11_fk_0012_it (fk_col) VALUES ('abc');
INSERT INTO t2_tc_11_fk_0012_it (fk_col) VALUES ('hello_world');
INSERT INTO t2_tc_11_fk_0012_it (fk_col) VALUES ('a');
SELECT 'TC-11-FK-0012-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0012_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0012_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0012_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0012_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0012_it a JOIN t2_tc_11_fk_0012_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-11-FK-0013-IP
-- FK Scenario: child, Algorithm: inplace
-- Type: VARCHAR(50) -> VARCHAR(100)
-- Expected: SUCCESS
-- Expected ALTER: SUCCESS
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0013_ip, tp_tc_11_fk_0013_ip, t2_tc_11_fk_0013_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0013_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0013_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0013_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0013_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0013_ip (fk_col) VALUES ('hello');
INSERT INTO tc_tc_11_fk_0013_ip (fk_col) VALUES ('hello');
INSERT INTO tp_tc_11_fk_0013_ip (fk_col) VALUES ('world');
INSERT INTO tc_tc_11_fk_0013_ip (fk_col) VALUES ('world');
INSERT INTO tp_tc_11_fk_0013_ip (fk_col) VALUES ('test');
INSERT INTO tc_tc_11_fk_0013_ip (fk_col) VALUES ('test');
INSERT INTO tp_tc_11_fk_0013_ip (fk_col) VALUES ('abc');
INSERT INTO tc_tc_11_fk_0013_ip (fk_col) VALUES ('abc');
-- ALTER child table only
ALTER TABLE tc_tc_11_fk_0013_ip MODIFY fk_col VARCHAR(100) CHARACTER SET latin1, ALGORITHM=inplace;
INSERT INTO tp_tc_11_fk_0013_ip (fk_col) VALUES ('hello_world');
INSERT INTO tc_tc_11_fk_0013_ip (fk_col) VALUES ('hello_world');
INSERT INTO tp_tc_11_fk_0013_ip (fk_col) VALUES ('a');
INSERT INTO tc_tc_11_fk_0013_ip (fk_col) VALUES ('a');
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0013_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARCHAR(100) CHARACTER SET latin1, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0013_ip (fk_col) VALUES ('hello');
INSERT INTO t2_tc_11_fk_0013_ip (fk_col) VALUES ('world');
INSERT INTO t2_tc_11_fk_0013_ip (fk_col) VALUES ('test');
INSERT INTO t2_tc_11_fk_0013_ip (fk_col) VALUES ('abc');
INSERT INTO t2_tc_11_fk_0013_ip (fk_col) VALUES ('hello_world');
INSERT INTO t2_tc_11_fk_0013_ip (fk_col) VALUES ('a');
SELECT 'TC-11-FK-0013-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0013_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0013_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0013_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0013_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0013_ip a JOIN t2_tc_11_fk_0013_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-11-FK-0014-IP
-- FK Scenario: parent, Algorithm: inplace
-- Type: VARCHAR(50) -> VARCHAR(100)
-- Expected: SUCCESS
-- Expected ALTER: SUCCESS
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0014_ip, tp_tc_11_fk_0014_ip, t2_tc_11_fk_0014_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0014_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0014_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0014_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0014_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0014_ip (fk_col) VALUES ('hello');
INSERT INTO tc_tc_11_fk_0014_ip (fk_col) VALUES ('hello');
INSERT INTO tp_tc_11_fk_0014_ip (fk_col) VALUES ('world');
INSERT INTO tc_tc_11_fk_0014_ip (fk_col) VALUES ('world');
INSERT INTO tp_tc_11_fk_0014_ip (fk_col) VALUES ('test');
INSERT INTO tc_tc_11_fk_0014_ip (fk_col) VALUES ('test');
INSERT INTO tp_tc_11_fk_0014_ip (fk_col) VALUES ('abc');
INSERT INTO tc_tc_11_fk_0014_ip (fk_col) VALUES ('abc');
-- ALTER parent table only
ALTER TABLE tp_tc_11_fk_0014_ip MODIFY fk_col VARCHAR(100) CHARACTER SET latin1, ALGORITHM=inplace;
INSERT INTO tp_tc_11_fk_0014_ip (fk_col) VALUES ('hello_world');
INSERT INTO tc_tc_11_fk_0014_ip (fk_col) VALUES ('hello_world');
INSERT INTO tp_tc_11_fk_0014_ip (fk_col) VALUES ('a');
INSERT INTO tc_tc_11_fk_0014_ip (fk_col) VALUES ('a');
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0014_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARCHAR(100) CHARACTER SET latin1, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0014_ip (fk_col) VALUES ('hello');
INSERT INTO t2_tc_11_fk_0014_ip (fk_col) VALUES ('world');
INSERT INTO t2_tc_11_fk_0014_ip (fk_col) VALUES ('test');
INSERT INTO t2_tc_11_fk_0014_ip (fk_col) VALUES ('abc');
INSERT INTO t2_tc_11_fk_0014_ip (fk_col) VALUES ('hello_world');
INSERT INTO t2_tc_11_fk_0014_ip (fk_col) VALUES ('a');
SELECT 'TC-11-FK-0014-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0014_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0014_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0014_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0014_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0014_ip a JOIN t2_tc_11_fk_0014_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-11-FK-0015-IP
-- FK Scenario: both, Algorithm: inplace
-- Type: VARCHAR(50) -> VARCHAR(100)
-- Expected: SUCCESS
-- Expected ALTER: SUCCESS
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0015_ip, tp_tc_11_fk_0015_ip, t2_tc_11_fk_0015_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0015_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0015_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0015_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0015_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0015_ip (fk_col) VALUES ('hello');
INSERT INTO tc_tc_11_fk_0015_ip (fk_col) VALUES ('hello');
INSERT INTO tp_tc_11_fk_0015_ip (fk_col) VALUES ('world');
INSERT INTO tc_tc_11_fk_0015_ip (fk_col) VALUES ('world');
INSERT INTO tp_tc_11_fk_0015_ip (fk_col) VALUES ('test');
INSERT INTO tc_tc_11_fk_0015_ip (fk_col) VALUES ('test');
INSERT INTO tp_tc_11_fk_0015_ip (fk_col) VALUES ('abc');
INSERT INTO tc_tc_11_fk_0015_ip (fk_col) VALUES ('abc');
-- ALTER both tables (parent first, then child)
ALTER TABLE tp_tc_11_fk_0015_ip MODIFY fk_col VARCHAR(100) CHARACTER SET latin1, ALGORITHM=inplace;
ALTER TABLE tc_tc_11_fk_0015_ip MODIFY fk_col VARCHAR(100) CHARACTER SET latin1, ALGORITHM=inplace;
INSERT INTO tp_tc_11_fk_0015_ip (fk_col) VALUES ('hello_world');
INSERT INTO tc_tc_11_fk_0015_ip (fk_col) VALUES ('hello_world');
INSERT INTO tp_tc_11_fk_0015_ip (fk_col) VALUES ('a');
INSERT INTO tc_tc_11_fk_0015_ip (fk_col) VALUES ('a');
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0015_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARCHAR(100) CHARACTER SET latin1, data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0015_ip (fk_col) VALUES ('hello');
INSERT INTO t2_tc_11_fk_0015_ip (fk_col) VALUES ('world');
INSERT INTO t2_tc_11_fk_0015_ip (fk_col) VALUES ('test');
INSERT INTO t2_tc_11_fk_0015_ip (fk_col) VALUES ('abc');
INSERT INTO t2_tc_11_fk_0015_ip (fk_col) VALUES ('hello_world');
INSERT INTO t2_tc_11_fk_0015_ip (fk_col) VALUES ('a');
SELECT 'TC-11-FK-0015-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0015_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0015_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0015_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0015_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0015_ip a JOIN t2_tc_11_fk_0015_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-11-FK-0016-IP
-- FK Scenario: non_fk, Algorithm: inplace
-- Type: VARCHAR(50) -> VARCHAR(100)
-- Expected: SUCCESS
-- Expected ALTER: SUCCESS
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_11_fk_0016_ip, tp_tc_11_fk_0016_ip, t2_tc_11_fk_0016_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_11_fk_0016_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_11_fk_0016_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARCHAR(50) CHARACTER SET latin1,
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_11_fk_0016_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_11_fk_0016_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_11_fk_0016_ip (fk_col) VALUES ('hello');
INSERT INTO tc_tc_11_fk_0016_ip (fk_col) VALUES ('hello');
INSERT INTO tp_tc_11_fk_0016_ip (fk_col) VALUES ('world');
INSERT INTO tc_tc_11_fk_0016_ip (fk_col) VALUES ('world');
INSERT INTO tp_tc_11_fk_0016_ip (fk_col) VALUES ('test');
INSERT INTO tc_tc_11_fk_0016_ip (fk_col) VALUES ('test');
INSERT INTO tp_tc_11_fk_0016_ip (fk_col) VALUES ('abc');
INSERT INTO tc_tc_11_fk_0016_ip (fk_col) VALUES ('abc');
-- ALTER non-FK column (data column)
ALTER TABLE tc_tc_11_fk_0016_ip MODIFY data VARCHAR(50) DEFAULT 'child', ALGORITHM=inplace;
INSERT INTO tp_tc_11_fk_0016_ip (fk_col) VALUES ('hello_world');
INSERT INTO tc_tc_11_fk_0016_ip (fk_col) VALUES ('hello_world');
INSERT INTO tp_tc_11_fk_0016_ip (fk_col) VALUES ('a');
INSERT INTO tc_tc_11_fk_0016_ip (fk_col) VALUES ('a');
-- Oracle table for child comparison
CREATE TABLE t2_tc_11_fk_0016_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARCHAR(50) CHARACTER SET latin1, data VARCHAR(50) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_11_fk_0016_ip (fk_col) VALUES ('hello');
INSERT INTO t2_tc_11_fk_0016_ip (fk_col) VALUES ('world');
INSERT INTO t2_tc_11_fk_0016_ip (fk_col) VALUES ('test');
INSERT INTO t2_tc_11_fk_0016_ip (fk_col) VALUES ('abc');
INSERT INTO t2_tc_11_fk_0016_ip (fk_col) VALUES ('hello_world');
INSERT INTO t2_tc_11_fk_0016_ip (fk_col) VALUES ('a');
SELECT 'TC-11-FK-0016-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_11_fk_0016_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_11_fk_0016_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_11_fk_0016_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_11_fk_0016_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_11_fk_0016_ip a JOIN t2_tc_11_fk_0016_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

