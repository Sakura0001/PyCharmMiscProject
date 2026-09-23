-- ============================================================
-- RDS MySQL DDL 秒级/在线修改列类型 测试套件 — 内网环境
-- 环境说明: 所有功能开关默认开启
-- 覆盖类型: BINARY + VARBINARY + DECIMAL + TEXT + BLOB + BIT
-- 覆盖算法: INSTANT + INPLACE (增强类型 INSTANT 预期成功: BINARY/VARBINARY/DECIMAL 已确认支持)
-- ============================================================
-- 本文件由 generate_test_sql.py 自动生成, 请勿手动修改
-- Suite-Revision: 59f7773ee801   (生成器源码哈希; 时间戳见 results/generation_manifest.json)
-- 用例 ID 规则: TC-<文件号>-<作用域>-<序号>-<IT|IP>  —— 全局唯一
--   作用域 REG=普通表 OFAT/二元组, ATR=列属性保持, SPE=特殊模式,
--          FK=外键, PTK=分区(目标列是分区键), PNK=分区(目标列非分区键)
-- ============================================================

SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET SESSION innodb_lock_wait_timeout = 50;

-- File 27: 外键表测试(增强类型)

-- Test Case: TC-27-FK-0001-IT
-- FK Scenario: child, Algorithm: instant
-- Type: BINARY(10) -> BINARY(20)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0001_it, tp_tc_27_fk_0001_it, t2_tc_27_fk_0001_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0001_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0001_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0001_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0001_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0001_it (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tc_tc_27_fk_0001_it (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tp_tc_27_fk_0001_it (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0001_it (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tp_tc_27_fk_0001_it (fk_col) VALUES (0x41424142414241424142);
INSERT INTO tc_tc_27_fk_0001_it (fk_col) VALUES (0x41424142414241424142);
-- ALTER child table only
ALTER TABLE tc_tc_27_fk_0001_it MODIFY fk_col BINARY(20), ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0001_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col BINARY(10), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0001_it (fk_col) VALUES (0x00000000000000000000);
INSERT INTO t2_tc_27_fk_0001_it (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_tc_27_fk_0001_it (fk_col) VALUES (0x41424142414241424142);
SELECT 'TC-27-FK-0001-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0001_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0001_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0001_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0001_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0001_it a JOIN t2_tc_27_fk_0001_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-27-FK-0002-IT
-- FK Scenario: parent, Algorithm: instant
-- Type: BINARY(10) -> BINARY(20)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0002_it, tp_tc_27_fk_0002_it, t2_tc_27_fk_0002_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0002_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0002_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0002_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0002_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0002_it (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tc_tc_27_fk_0002_it (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tp_tc_27_fk_0002_it (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0002_it (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tp_tc_27_fk_0002_it (fk_col) VALUES (0x41424142414241424142);
INSERT INTO tc_tc_27_fk_0002_it (fk_col) VALUES (0x41424142414241424142);
-- ALTER parent table only
ALTER TABLE tp_tc_27_fk_0002_it MODIFY fk_col BINARY(20), ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0002_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col BINARY(10), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0002_it (fk_col) VALUES (0x00000000000000000000);
INSERT INTO t2_tc_27_fk_0002_it (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_tc_27_fk_0002_it (fk_col) VALUES (0x41424142414241424142);
SELECT 'TC-27-FK-0002-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0002_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0002_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0002_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0002_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0002_it a JOIN t2_tc_27_fk_0002_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-27-FK-0003-IT
-- FK Scenario: both, Algorithm: instant
-- Type: BINARY(10) -> BINARY(20)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0003_it, tp_tc_27_fk_0003_it, t2_tc_27_fk_0003_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0003_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0003_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0003_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0003_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0003_it (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tc_tc_27_fk_0003_it (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tp_tc_27_fk_0003_it (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0003_it (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tp_tc_27_fk_0003_it (fk_col) VALUES (0x41424142414241424142);
INSERT INTO tc_tc_27_fk_0003_it (fk_col) VALUES (0x41424142414241424142);
-- ALTER both tables (parent first, then child)
ALTER TABLE tp_tc_27_fk_0003_it MODIFY fk_col BINARY(20), ALGORITHM=instant;
ALTER TABLE tc_tc_27_fk_0003_it MODIFY fk_col BINARY(20), ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0003_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col BINARY(10), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0003_it (fk_col) VALUES (0x00000000000000000000);
INSERT INTO t2_tc_27_fk_0003_it (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_tc_27_fk_0003_it (fk_col) VALUES (0x41424142414241424142);
SELECT 'TC-27-FK-0003-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0003_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0003_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0003_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0003_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0003_it a JOIN t2_tc_27_fk_0003_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-27-FK-0004-IT
-- FK Scenario: non_fk, Algorithm: instant
-- Type: BINARY(10) -> BINARY(20)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0004_it, tp_tc_27_fk_0004_it, t2_tc_27_fk_0004_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0004_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0004_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0004_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0004_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0004_it (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tc_tc_27_fk_0004_it (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tp_tc_27_fk_0004_it (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0004_it (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tp_tc_27_fk_0004_it (fk_col) VALUES (0x41424142414241424142);
INSERT INTO tc_tc_27_fk_0004_it (fk_col) VALUES (0x41424142414241424142);
-- ALTER non-FK column (data column)
ALTER TABLE tc_tc_27_fk_0004_it MODIFY data VARCHAR(50) DEFAULT 'child', ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0004_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col BINARY(10), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0004_it (fk_col) VALUES (0x00000000000000000000);
INSERT INTO t2_tc_27_fk_0004_it (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_tc_27_fk_0004_it (fk_col) VALUES (0x41424142414241424142);
SELECT 'TC-27-FK-0004-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0004_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0004_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0004_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0004_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0004_it a JOIN t2_tc_27_fk_0004_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-27-FK-0005-IP
-- FK Scenario: child, Algorithm: inplace
-- Type: BINARY(10) -> BINARY(20)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0005_ip, tp_tc_27_fk_0005_ip, t2_tc_27_fk_0005_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0005_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0005_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0005_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0005_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0005_ip (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tc_tc_27_fk_0005_ip (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tp_tc_27_fk_0005_ip (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0005_ip (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tp_tc_27_fk_0005_ip (fk_col) VALUES (0x41424142414241424142);
INSERT INTO tc_tc_27_fk_0005_ip (fk_col) VALUES (0x41424142414241424142);
-- ALTER child table only
ALTER TABLE tc_tc_27_fk_0005_ip MODIFY fk_col BINARY(20), ALGORITHM=inplace;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0005_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col BINARY(10), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0005_ip (fk_col) VALUES (0x00000000000000000000);
INSERT INTO t2_tc_27_fk_0005_ip (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_tc_27_fk_0005_ip (fk_col) VALUES (0x41424142414241424142);
SELECT 'TC-27-FK-0005-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0005_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0005_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0005_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0005_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0005_ip a JOIN t2_tc_27_fk_0005_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-27-FK-0006-IP
-- FK Scenario: parent, Algorithm: inplace
-- Type: BINARY(10) -> BINARY(20)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0006_ip, tp_tc_27_fk_0006_ip, t2_tc_27_fk_0006_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0006_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0006_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0006_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0006_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0006_ip (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tc_tc_27_fk_0006_ip (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tp_tc_27_fk_0006_ip (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0006_ip (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tp_tc_27_fk_0006_ip (fk_col) VALUES (0x41424142414241424142);
INSERT INTO tc_tc_27_fk_0006_ip (fk_col) VALUES (0x41424142414241424142);
-- ALTER parent table only
ALTER TABLE tp_tc_27_fk_0006_ip MODIFY fk_col BINARY(20), ALGORITHM=inplace;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0006_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col BINARY(10), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0006_ip (fk_col) VALUES (0x00000000000000000000);
INSERT INTO t2_tc_27_fk_0006_ip (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_tc_27_fk_0006_ip (fk_col) VALUES (0x41424142414241424142);
SELECT 'TC-27-FK-0006-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0006_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0006_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0006_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0006_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0006_ip a JOIN t2_tc_27_fk_0006_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-27-FK-0007-IP
-- FK Scenario: both, Algorithm: inplace
-- Type: BINARY(10) -> BINARY(20)
-- Expected: SUCCESS
-- Expected ALTER: SUCCESS
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0007_ip, tp_tc_27_fk_0007_ip, t2_tc_27_fk_0007_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0007_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0007_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0007_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0007_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0007_ip (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tc_tc_27_fk_0007_ip (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tp_tc_27_fk_0007_ip (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0007_ip (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tp_tc_27_fk_0007_ip (fk_col) VALUES (0x41424142414241424142);
INSERT INTO tc_tc_27_fk_0007_ip (fk_col) VALUES (0x41424142414241424142);
-- ALTER both tables (parent first, then child)
ALTER TABLE tp_tc_27_fk_0007_ip MODIFY fk_col BINARY(20), ALGORITHM=inplace;
ALTER TABLE tc_tc_27_fk_0007_ip MODIFY fk_col BINARY(20), ALGORITHM=inplace;
INSERT INTO tp_tc_27_fk_0007_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0007_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO tp_tc_27_fk_0007_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0007_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0007_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col BINARY(20), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0007_ip (fk_col) VALUES (0x00000000000000000000);
INSERT INTO t2_tc_27_fk_0007_ip (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_tc_27_fk_0007_ip (fk_col) VALUES (0x41424142414241424142);
INSERT INTO t2_tc_27_fk_0007_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_tc_27_fk_0007_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
SELECT 'TC-27-FK-0007-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0007_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0007_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0007_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0007_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0007_ip a JOIN t2_tc_27_fk_0007_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-27-FK-0008-IP
-- FK Scenario: non_fk, Algorithm: inplace
-- Type: BINARY(10) -> BINARY(20)
-- Expected: SUCCESS
-- Expected ALTER: SUCCESS
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0008_ip, tp_tc_27_fk_0008_ip, t2_tc_27_fk_0008_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0008_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0008_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col BINARY(10),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0008_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0008_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0008_ip (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tc_tc_27_fk_0008_ip (fk_col) VALUES (0x00000000000000000000);
INSERT INTO tp_tc_27_fk_0008_ip (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0008_ip (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO tp_tc_27_fk_0008_ip (fk_col) VALUES (0x41424142414241424142);
INSERT INTO tc_tc_27_fk_0008_ip (fk_col) VALUES (0x41424142414241424142);
-- ALTER non-FK column (data column)
ALTER TABLE tc_tc_27_fk_0008_ip MODIFY data VARCHAR(50) DEFAULT 'child', ALGORITHM=inplace;
INSERT INTO tp_tc_27_fk_0008_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0008_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO tp_tc_27_fk_0008_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0008_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0008_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col BINARY(10), data VARCHAR(50) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0008_ip (fk_col) VALUES (0x00000000000000000000);
INSERT INTO t2_tc_27_fk_0008_ip (fk_col) VALUES (0xffffffffffffffffffff);
INSERT INTO t2_tc_27_fk_0008_ip (fk_col) VALUES (0x41424142414241424142);
INSERT INTO t2_tc_27_fk_0008_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000);
INSERT INTO t2_tc_27_fk_0008_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffff);
SELECT 'TC-27-FK-0008-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0008_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0008_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0008_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0008_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0008_ip a JOIN t2_tc_27_fk_0008_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-27-FK-0009-IT
-- FK Scenario: child, Algorithm: instant
-- Type: VARBINARY(50) -> VARBINARY(100)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0009_it, tp_tc_27_fk_0009_it, t2_tc_27_fk_0009_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0009_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0009_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0009_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0009_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0009_it (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0009_it (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tp_tc_27_fk_0009_it (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0009_it (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- ALTER child table only
ALTER TABLE tc_tc_27_fk_0009_it MODIFY fk_col VARBINARY(100), ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0009_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARBINARY(50), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0009_it (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_tc_27_fk_0009_it (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
SELECT 'TC-27-FK-0009-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0009_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0009_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0009_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0009_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0009_it a JOIN t2_tc_27_fk_0009_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-27-FK-0010-IT
-- FK Scenario: parent, Algorithm: instant
-- Type: VARBINARY(50) -> VARBINARY(100)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0010_it, tp_tc_27_fk_0010_it, t2_tc_27_fk_0010_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0010_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0010_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0010_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0010_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0010_it (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0010_it (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tp_tc_27_fk_0010_it (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0010_it (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- ALTER parent table only
ALTER TABLE tp_tc_27_fk_0010_it MODIFY fk_col VARBINARY(100), ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0010_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARBINARY(50), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0010_it (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_tc_27_fk_0010_it (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
SELECT 'TC-27-FK-0010-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0010_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0010_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0010_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0010_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0010_it a JOIN t2_tc_27_fk_0010_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-27-FK-0011-IT
-- FK Scenario: both, Algorithm: instant
-- Type: VARBINARY(50) -> VARBINARY(100)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0011_it, tp_tc_27_fk_0011_it, t2_tc_27_fk_0011_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0011_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0011_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0011_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0011_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0011_it (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0011_it (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tp_tc_27_fk_0011_it (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0011_it (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- ALTER both tables (parent first, then child)
ALTER TABLE tp_tc_27_fk_0011_it MODIFY fk_col VARBINARY(100), ALGORITHM=instant;
ALTER TABLE tc_tc_27_fk_0011_it MODIFY fk_col VARBINARY(100), ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0011_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARBINARY(50), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0011_it (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_tc_27_fk_0011_it (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
SELECT 'TC-27-FK-0011-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0011_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0011_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0011_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0011_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0011_it a JOIN t2_tc_27_fk_0011_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-27-FK-0012-IT
-- FK Scenario: non_fk, Algorithm: instant
-- Type: VARBINARY(50) -> VARBINARY(100)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0012_it, tp_tc_27_fk_0012_it, t2_tc_27_fk_0012_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0012_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0012_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0012_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0012_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0012_it (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0012_it (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tp_tc_27_fk_0012_it (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0012_it (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- ALTER non-FK column (data column)
ALTER TABLE tc_tc_27_fk_0012_it MODIFY data VARCHAR(50) DEFAULT 'child', ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0012_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARBINARY(50), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0012_it (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_tc_27_fk_0012_it (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
SELECT 'TC-27-FK-0012-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0012_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0012_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0012_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0012_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0012_it a JOIN t2_tc_27_fk_0012_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-27-FK-0013-IP
-- FK Scenario: child, Algorithm: inplace
-- Type: VARBINARY(50) -> VARBINARY(100)
-- Expected: SUCCESS
-- Expected ALTER: SUCCESS
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0013_ip, tp_tc_27_fk_0013_ip, t2_tc_27_fk_0013_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0013_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0013_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0013_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0013_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0013_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0013_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tp_tc_27_fk_0013_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0013_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- ALTER child table only
ALTER TABLE tc_tc_27_fk_0013_ip MODIFY fk_col VARBINARY(100), ALGORITHM=inplace;
INSERT INTO tp_tc_27_fk_0013_ip (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0013_ip (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0013_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARBINARY(100), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0013_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_tc_27_fk_0013_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_tc_27_fk_0013_ip (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
SELECT 'TC-27-FK-0013-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0013_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0013_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0013_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0013_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0013_ip a JOIN t2_tc_27_fk_0013_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-27-FK-0014-IP
-- FK Scenario: parent, Algorithm: inplace
-- Type: VARBINARY(50) -> VARBINARY(100)
-- Expected: SUCCESS
-- Expected ALTER: SUCCESS
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0014_ip, tp_tc_27_fk_0014_ip, t2_tc_27_fk_0014_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0014_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0014_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0014_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0014_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0014_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0014_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tp_tc_27_fk_0014_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0014_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- ALTER parent table only
ALTER TABLE tp_tc_27_fk_0014_ip MODIFY fk_col VARBINARY(100), ALGORITHM=inplace;
INSERT INTO tp_tc_27_fk_0014_ip (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0014_ip (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0014_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARBINARY(100), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0014_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_tc_27_fk_0014_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_tc_27_fk_0014_ip (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
SELECT 'TC-27-FK-0014-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0014_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0014_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0014_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0014_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0014_ip a JOIN t2_tc_27_fk_0014_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-27-FK-0015-IP
-- FK Scenario: both, Algorithm: inplace
-- Type: VARBINARY(50) -> VARBINARY(100)
-- Expected: SUCCESS
-- Expected ALTER: SUCCESS
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0015_ip, tp_tc_27_fk_0015_ip, t2_tc_27_fk_0015_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0015_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0015_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0015_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0015_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0015_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0015_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tp_tc_27_fk_0015_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0015_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- ALTER both tables (parent first, then child)
ALTER TABLE tp_tc_27_fk_0015_ip MODIFY fk_col VARBINARY(100), ALGORITHM=inplace;
ALTER TABLE tc_tc_27_fk_0015_ip MODIFY fk_col VARBINARY(100), ALGORITHM=inplace;
INSERT INTO tp_tc_27_fk_0015_ip (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0015_ip (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0015_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARBINARY(100), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0015_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_tc_27_fk_0015_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_tc_27_fk_0015_ip (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
SELECT 'TC-27-FK-0015-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0015_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0015_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0015_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0015_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0015_ip a JOIN t2_tc_27_fk_0015_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-27-FK-0016-IP
-- FK Scenario: non_fk, Algorithm: inplace
-- Type: VARBINARY(50) -> VARBINARY(100)
-- Expected: SUCCESS
-- Expected ALTER: SUCCESS
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0016_ip, tp_tc_27_fk_0016_ip, t2_tc_27_fk_0016_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0016_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0016_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col VARBINARY(50),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0016_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0016_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0016_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0016_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tp_tc_27_fk_0016_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO tc_tc_27_fk_0016_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
-- ALTER non-FK column (data column)
ALTER TABLE tc_tc_27_fk_0016_ip MODIFY data VARCHAR(50) DEFAULT 'child', ALGORITHM=inplace;
INSERT INTO tp_tc_27_fk_0016_ip (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO tc_tc_27_fk_0016_ip (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0016_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col VARBINARY(50), data VARCHAR(50) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0016_ip (fk_col) VALUES (0x0000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
INSERT INTO t2_tc_27_fk_0016_ip (fk_col) VALUES (0xffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffffff);
INSERT INTO t2_tc_27_fk_0016_ip (fk_col) VALUES (0x00000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000);
SELECT 'TC-27-FK-0016-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0016_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0016_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0016_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0016_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0016_ip a JOIN t2_tc_27_fk_0016_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-27-FK-0017-IT
-- FK Scenario: child, Algorithm: instant
-- Type: DECIMAL(10,2) -> DECIMAL(12,2)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0017_it, tp_tc_27_fk_0017_it, t2_tc_27_fk_0017_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0017_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0017_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0017_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0017_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0017_it (fk_col) VALUES (0.00);
INSERT INTO tc_tc_27_fk_0017_it (fk_col) VALUES (0.00);
INSERT INTO tp_tc_27_fk_0017_it (fk_col) VALUES (1.23);
INSERT INTO tc_tc_27_fk_0017_it (fk_col) VALUES (1.23);
INSERT INTO tp_tc_27_fk_0017_it (fk_col) VALUES (-1.23);
INSERT INTO tc_tc_27_fk_0017_it (fk_col) VALUES (-1.23);
INSERT INTO tp_tc_27_fk_0017_it (fk_col) VALUES (99.99);
INSERT INTO tc_tc_27_fk_0017_it (fk_col) VALUES (99.99);
-- ALTER child table only
ALTER TABLE tc_tc_27_fk_0017_it MODIFY fk_col DECIMAL(12,2), ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0017_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col DECIMAL(10,2), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0017_it (fk_col) VALUES (0.00);
INSERT INTO t2_tc_27_fk_0017_it (fk_col) VALUES (1.23);
INSERT INTO t2_tc_27_fk_0017_it (fk_col) VALUES (-1.23);
INSERT INTO t2_tc_27_fk_0017_it (fk_col) VALUES (99.99);
SELECT 'TC-27-FK-0017-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0017_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0017_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0017_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0017_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0017_it a JOIN t2_tc_27_fk_0017_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-27-FK-0018-IT
-- FK Scenario: parent, Algorithm: instant
-- Type: DECIMAL(10,2) -> DECIMAL(12,2)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0018_it, tp_tc_27_fk_0018_it, t2_tc_27_fk_0018_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0018_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0018_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0018_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0018_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0018_it (fk_col) VALUES (0.00);
INSERT INTO tc_tc_27_fk_0018_it (fk_col) VALUES (0.00);
INSERT INTO tp_tc_27_fk_0018_it (fk_col) VALUES (1.23);
INSERT INTO tc_tc_27_fk_0018_it (fk_col) VALUES (1.23);
INSERT INTO tp_tc_27_fk_0018_it (fk_col) VALUES (-1.23);
INSERT INTO tc_tc_27_fk_0018_it (fk_col) VALUES (-1.23);
INSERT INTO tp_tc_27_fk_0018_it (fk_col) VALUES (99.99);
INSERT INTO tc_tc_27_fk_0018_it (fk_col) VALUES (99.99);
-- ALTER parent table only
ALTER TABLE tp_tc_27_fk_0018_it MODIFY fk_col DECIMAL(12,2), ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0018_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col DECIMAL(10,2), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0018_it (fk_col) VALUES (0.00);
INSERT INTO t2_tc_27_fk_0018_it (fk_col) VALUES (1.23);
INSERT INTO t2_tc_27_fk_0018_it (fk_col) VALUES (-1.23);
INSERT INTO t2_tc_27_fk_0018_it (fk_col) VALUES (99.99);
SELECT 'TC-27-FK-0018-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0018_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0018_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0018_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0018_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0018_it a JOIN t2_tc_27_fk_0018_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-27-FK-0019-IT
-- FK Scenario: both, Algorithm: instant
-- Type: DECIMAL(10,2) -> DECIMAL(12,2)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0019_it, tp_tc_27_fk_0019_it, t2_tc_27_fk_0019_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0019_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0019_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0019_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0019_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0019_it (fk_col) VALUES (0.00);
INSERT INTO tc_tc_27_fk_0019_it (fk_col) VALUES (0.00);
INSERT INTO tp_tc_27_fk_0019_it (fk_col) VALUES (1.23);
INSERT INTO tc_tc_27_fk_0019_it (fk_col) VALUES (1.23);
INSERT INTO tp_tc_27_fk_0019_it (fk_col) VALUES (-1.23);
INSERT INTO tc_tc_27_fk_0019_it (fk_col) VALUES (-1.23);
INSERT INTO tp_tc_27_fk_0019_it (fk_col) VALUES (99.99);
INSERT INTO tc_tc_27_fk_0019_it (fk_col) VALUES (99.99);
-- ALTER both tables (parent first, then child)
ALTER TABLE tp_tc_27_fk_0019_it MODIFY fk_col DECIMAL(12,2), ALGORITHM=instant;
ALTER TABLE tc_tc_27_fk_0019_it MODIFY fk_col DECIMAL(12,2), ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0019_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col DECIMAL(10,2), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0019_it (fk_col) VALUES (0.00);
INSERT INTO t2_tc_27_fk_0019_it (fk_col) VALUES (1.23);
INSERT INTO t2_tc_27_fk_0019_it (fk_col) VALUES (-1.23);
INSERT INTO t2_tc_27_fk_0019_it (fk_col) VALUES (99.99);
SELECT 'TC-27-FK-0019-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0019_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0019_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0019_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0019_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0019_it a JOIN t2_tc_27_fk_0019_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-27-FK-0020-IT
-- FK Scenario: non_fk, Algorithm: instant
-- Type: DECIMAL(10,2) -> DECIMAL(12,2)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0020_it, tp_tc_27_fk_0020_it, t2_tc_27_fk_0020_it;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0020_it (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0020_it (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0020_it_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0020_it(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0020_it (fk_col) VALUES (0.00);
INSERT INTO tc_tc_27_fk_0020_it (fk_col) VALUES (0.00);
INSERT INTO tp_tc_27_fk_0020_it (fk_col) VALUES (1.23);
INSERT INTO tc_tc_27_fk_0020_it (fk_col) VALUES (1.23);
INSERT INTO tp_tc_27_fk_0020_it (fk_col) VALUES (-1.23);
INSERT INTO tc_tc_27_fk_0020_it (fk_col) VALUES (-1.23);
INSERT INTO tp_tc_27_fk_0020_it (fk_col) VALUES (99.99);
INSERT INTO tc_tc_27_fk_0020_it (fk_col) VALUES (99.99);
-- ALTER non-FK column (data column)
ALTER TABLE tc_tc_27_fk_0020_it MODIFY data VARCHAR(50) DEFAULT 'child', ALGORITHM=instant;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0020_it (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col DECIMAL(10,2), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0020_it (fk_col) VALUES (0.00);
INSERT INTO t2_tc_27_fk_0020_it (fk_col) VALUES (1.23);
INSERT INTO t2_tc_27_fk_0020_it (fk_col) VALUES (-1.23);
INSERT INTO t2_tc_27_fk_0020_it (fk_col) VALUES (99.99);
SELECT 'TC-27-FK-0020-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0020_it
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0020_it)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0020_it
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0020_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0020_it a JOIN t2_tc_27_fk_0020_it b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-27-FK-0021-IP
-- FK Scenario: child, Algorithm: inplace
-- Type: DECIMAL(10,2) -> DECIMAL(12,2)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0021_ip, tp_tc_27_fk_0021_ip, t2_tc_27_fk_0021_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0021_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0021_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0021_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0021_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0021_ip (fk_col) VALUES (0.00);
INSERT INTO tc_tc_27_fk_0021_ip (fk_col) VALUES (0.00);
INSERT INTO tp_tc_27_fk_0021_ip (fk_col) VALUES (1.23);
INSERT INTO tc_tc_27_fk_0021_ip (fk_col) VALUES (1.23);
INSERT INTO tp_tc_27_fk_0021_ip (fk_col) VALUES (-1.23);
INSERT INTO tc_tc_27_fk_0021_ip (fk_col) VALUES (-1.23);
INSERT INTO tp_tc_27_fk_0021_ip (fk_col) VALUES (99.99);
INSERT INTO tc_tc_27_fk_0021_ip (fk_col) VALUES (99.99);
-- ALTER child table only
ALTER TABLE tc_tc_27_fk_0021_ip MODIFY fk_col DECIMAL(12,2), ALGORITHM=inplace;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0021_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col DECIMAL(10,2), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0021_ip (fk_col) VALUES (0.00);
INSERT INTO t2_tc_27_fk_0021_ip (fk_col) VALUES (1.23);
INSERT INTO t2_tc_27_fk_0021_ip (fk_col) VALUES (-1.23);
INSERT INTO t2_tc_27_fk_0021_ip (fk_col) VALUES (99.99);
SELECT 'TC-27-FK-0021-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0021_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0021_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0021_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0021_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0021_ip a JOIN t2_tc_27_fk_0021_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-27-FK-0022-IP
-- FK Scenario: parent, Algorithm: inplace
-- Type: DECIMAL(10,2) -> DECIMAL(12,2)
-- Expected: FAIL
-- Expected ALTER: FAIL
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0022_ip, tp_tc_27_fk_0022_ip, t2_tc_27_fk_0022_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0022_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0022_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0022_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0022_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0022_ip (fk_col) VALUES (0.00);
INSERT INTO tc_tc_27_fk_0022_ip (fk_col) VALUES (0.00);
INSERT INTO tp_tc_27_fk_0022_ip (fk_col) VALUES (1.23);
INSERT INTO tc_tc_27_fk_0022_ip (fk_col) VALUES (1.23);
INSERT INTO tp_tc_27_fk_0022_ip (fk_col) VALUES (-1.23);
INSERT INTO tc_tc_27_fk_0022_ip (fk_col) VALUES (-1.23);
INSERT INTO tp_tc_27_fk_0022_ip (fk_col) VALUES (99.99);
INSERT INTO tc_tc_27_fk_0022_ip (fk_col) VALUES (99.99);
-- ALTER parent table only
ALTER TABLE tp_tc_27_fk_0022_ip MODIFY fk_col DECIMAL(12,2), ALGORITHM=inplace;
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0022_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col DECIMAL(10,2), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0022_ip (fk_col) VALUES (0.00);
INSERT INTO t2_tc_27_fk_0022_ip (fk_col) VALUES (1.23);
INSERT INTO t2_tc_27_fk_0022_ip (fk_col) VALUES (-1.23);
INSERT INTO t2_tc_27_fk_0022_ip (fk_col) VALUES (99.99);
SELECT 'TC-27-FK-0022-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0022_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0022_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0022_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0022_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0022_ip a JOIN t2_tc_27_fk_0022_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-27-FK-0023-IP
-- FK Scenario: both, Algorithm: inplace
-- Type: DECIMAL(10,2) -> DECIMAL(12,2)
-- Expected: SUCCESS
-- Expected ALTER: SUCCESS
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0023_ip, tp_tc_27_fk_0023_ip, t2_tc_27_fk_0023_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0023_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0023_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0023_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0023_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0023_ip (fk_col) VALUES (0.00);
INSERT INTO tc_tc_27_fk_0023_ip (fk_col) VALUES (0.00);
INSERT INTO tp_tc_27_fk_0023_ip (fk_col) VALUES (1.23);
INSERT INTO tc_tc_27_fk_0023_ip (fk_col) VALUES (1.23);
INSERT INTO tp_tc_27_fk_0023_ip (fk_col) VALUES (-1.23);
INSERT INTO tc_tc_27_fk_0023_ip (fk_col) VALUES (-1.23);
INSERT INTO tp_tc_27_fk_0023_ip (fk_col) VALUES (99.99);
INSERT INTO tc_tc_27_fk_0023_ip (fk_col) VALUES (99.99);
-- ALTER both tables (parent first, then child)
ALTER TABLE tp_tc_27_fk_0023_ip MODIFY fk_col DECIMAL(12,2), ALGORITHM=inplace;
ALTER TABLE tc_tc_27_fk_0023_ip MODIFY fk_col DECIMAL(12,2), ALGORITHM=inplace;
INSERT INTO tp_tc_27_fk_0023_ip (fk_col) VALUES (999.99);
INSERT INTO tc_tc_27_fk_0023_ip (fk_col) VALUES (999.99);
INSERT INTO tp_tc_27_fk_0023_ip (fk_col) VALUES (1000.00);
INSERT INTO tc_tc_27_fk_0023_ip (fk_col) VALUES (1000.00);
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0023_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col DECIMAL(12,2), data VARCHAR(20) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0023_ip (fk_col) VALUES (0.00);
INSERT INTO t2_tc_27_fk_0023_ip (fk_col) VALUES (1.23);
INSERT INTO t2_tc_27_fk_0023_ip (fk_col) VALUES (-1.23);
INSERT INTO t2_tc_27_fk_0023_ip (fk_col) VALUES (99.99);
INSERT INTO t2_tc_27_fk_0023_ip (fk_col) VALUES (999.99);
INSERT INTO t2_tc_27_fk_0023_ip (fk_col) VALUES (1000.00);
SELECT 'TC-27-FK-0023-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0023_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0023_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0023_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0023_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0023_ip a JOIN t2_tc_27_fk_0023_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

-- Test Case: TC-27-FK-0024-IP
-- FK Scenario: non_fk, Algorithm: inplace
-- Type: DECIMAL(10,2) -> DECIMAL(12,2)
-- Expected: SUCCESS
-- Expected ALTER: SUCCESS
SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET foreign_key_checks=0;
DROP TABLE IF EXISTS tc_tc_27_fk_0024_ip, tp_tc_27_fk_0024_ip, t2_tc_27_fk_0024_ip;
SET foreign_key_checks=1;
CREATE TABLE tp_tc_27_fk_0024_ip (
  pid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'parent',
  INDEX idx_parent_fk (fk_col)
) ENGINE=InnoDB;
CREATE TABLE tc_tc_27_fk_0024_ip (
  cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  fk_col DECIMAL(10,2),
  data VARCHAR(20) DEFAULT 'child',
  INDEX idx_fk (fk_col),
  CONSTRAINT tc_27_fk_0024_ip_fk FOREIGN KEY (fk_col) REFERENCES tp_tc_27_fk_0024_ip(fk_col)
) ENGINE=InnoDB;
INSERT INTO tp_tc_27_fk_0024_ip (fk_col) VALUES (0.00);
INSERT INTO tc_tc_27_fk_0024_ip (fk_col) VALUES (0.00);
INSERT INTO tp_tc_27_fk_0024_ip (fk_col) VALUES (1.23);
INSERT INTO tc_tc_27_fk_0024_ip (fk_col) VALUES (1.23);
INSERT INTO tp_tc_27_fk_0024_ip (fk_col) VALUES (-1.23);
INSERT INTO tc_tc_27_fk_0024_ip (fk_col) VALUES (-1.23);
INSERT INTO tp_tc_27_fk_0024_ip (fk_col) VALUES (99.99);
INSERT INTO tc_tc_27_fk_0024_ip (fk_col) VALUES (99.99);
-- ALTER non-FK column (data column)
ALTER TABLE tc_tc_27_fk_0024_ip MODIFY data VARCHAR(50) DEFAULT 'child', ALGORITHM=inplace;
INSERT INTO tp_tc_27_fk_0024_ip (fk_col) VALUES (999.99);
INSERT INTO tc_tc_27_fk_0024_ip (fk_col) VALUES (999.99);
INSERT INTO tp_tc_27_fk_0024_ip (fk_col) VALUES (1000.00);
INSERT INTO tc_tc_27_fk_0024_ip (fk_col) VALUES (1000.00);
-- Oracle table for child comparison
CREATE TABLE t2_tc_27_fk_0024_ip (cid INT NOT NULL AUTO_INCREMENT PRIMARY KEY, fk_col DECIMAL(10,2), data VARCHAR(50) DEFAULT 'child') ENGINE=InnoDB;
INSERT INTO t2_tc_27_fk_0024_ip (fk_col) VALUES (0.00);
INSERT INTO t2_tc_27_fk_0024_ip (fk_col) VALUES (1.23);
INSERT INTO t2_tc_27_fk_0024_ip (fk_col) VALUES (-1.23);
INSERT INTO t2_tc_27_fk_0024_ip (fk_col) VALUES (99.99);
INSERT INTO t2_tc_27_fk_0024_ip (fk_col) VALUES (999.99);
INSERT INTO t2_tc_27_fk_0024_ip (fk_col) VALUES (1000.00);
SELECT 'TC-27-FK-0024-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',cid) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, cid FROM tc_tc_27_fk_0024_ip
   WHERE cid NOT IN (SELECT cid FROM t2_tc_27_fk_0024_ip)
  UNION ALL
  SELECT 't2_extra' AS src, cid FROM t2_tc_27_fk_0024_ip
   WHERE cid NOT IN (SELECT cid FROM tc_tc_27_fk_0024_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.cid FROM tc_tc_27_fk_0024_ip a JOIN t2_tc_27_fk_0024_ip b ON a.cid = b.cid
   WHERE NOT (a.fk_col <=> b.fk_col AND a.data <=> b.data)
) AS mismatches;

