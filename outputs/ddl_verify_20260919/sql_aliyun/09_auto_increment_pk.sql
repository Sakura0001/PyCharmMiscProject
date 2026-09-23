-- ============================================================
-- RDS MySQL DDL 秒级/在线修改列类型 测试套件 — 阿里云环境
-- 环境说明: 所有功能开关默认开启
-- 覆盖类型: 整数(SIGNED/UNSIGNED) + CHAR + VARCHAR
-- 覆盖算法: INSTANT + INPLACE
-- ============================================================
-- 本文件由 generate_test_sql.py 自动生成, 请勿手动修改
-- Suite-Revision: 4dfbe1e59c0b   (生成器源码哈希; 时间戳见 results/generation_manifest.json)
-- 用例 ID 规则: TC-<文件号>-<作用域>-<序号>-<IT|IP>  —— 全局唯一
--   作用域 REG=普通表 OFAT/二元组, ATR=列属性保持, SPE=特殊模式,
--          FK=外键, PTK=分区(目标列是分区键), PNK=分区(目标列非分区键)
-- ============================================================

SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET SESSION innodb_lock_wait_timeout = 50;

-- File 09: AUTO_INCREMENT PK 扩容专项

-- Test Case: TC-09-ATR-0001-IT
-- Column attribute preservation: AUTO_INCREMENT
-- Type: TINYINT -> SMALLINT, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_09_atr_0001_it, t2_tc_09_atr_0001_it;
CREATE TABLE t1_tc_09_atr_0001_it (
  id TINYINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0001_it (id) VALUES (-128);
INSERT INTO t1_tc_09_atr_0001_it (id) VALUES (127);
INSERT INTO t1_tc_09_atr_0001_it (id) VALUES (-127);
INSERT INTO t1_tc_09_atr_0001_it (id) VALUES (126);
INSERT INTO t1_tc_09_atr_0001_it (id) VALUES (0);
ALTER TABLE t1_tc_09_atr_0001_it MODIFY id SMALLINT NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_09_atr_0001_it (id) VALUES (-32768);
INSERT INTO t1_tc_09_atr_0001_it (id) VALUES (-32767);
INSERT INTO t1_tc_09_atr_0001_it (id) VALUES (32767);
SELECT 'TC-09-ATR-0001-IT' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0001_it' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0002-IP
-- Column attribute preservation: AUTO_INCREMENT
-- Type: TINYINT -> SMALLINT, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_09_atr_0002_ip, t2_tc_09_atr_0002_ip;
CREATE TABLE t1_tc_09_atr_0002_ip (
  id TINYINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0002_ip (id) VALUES (-128);
INSERT INTO t1_tc_09_atr_0002_ip (id) VALUES (127);
INSERT INTO t1_tc_09_atr_0002_ip (id) VALUES (-127);
INSERT INTO t1_tc_09_atr_0002_ip (id) VALUES (126);
INSERT INTO t1_tc_09_atr_0002_ip (id) VALUES (0);
ALTER TABLE t1_tc_09_atr_0002_ip MODIFY id SMALLINT NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_09_atr_0002_ip (id) VALUES (-32768);
INSERT INTO t1_tc_09_atr_0002_ip (id) VALUES (-32767);
INSERT INTO t1_tc_09_atr_0002_ip (id) VALUES (32767);
SELECT 'TC-09-ATR-0002-IP' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0002_ip' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0003-IT
-- Column attribute preservation: AUTO_INCREMENT
-- Type: TINYINT -> MEDIUMINT, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_09_atr_0003_it, t2_tc_09_atr_0003_it;
CREATE TABLE t1_tc_09_atr_0003_it (
  id TINYINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0003_it (id) VALUES (-128);
INSERT INTO t1_tc_09_atr_0003_it (id) VALUES (127);
INSERT INTO t1_tc_09_atr_0003_it (id) VALUES (-127);
INSERT INTO t1_tc_09_atr_0003_it (id) VALUES (126);
INSERT INTO t1_tc_09_atr_0003_it (id) VALUES (0);
ALTER TABLE t1_tc_09_atr_0003_it MODIFY id MEDIUMINT NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_09_atr_0003_it (id) VALUES (-8388608);
INSERT INTO t1_tc_09_atr_0003_it (id) VALUES (-8388607);
INSERT INTO t1_tc_09_atr_0003_it (id) VALUES (8388607);
SELECT 'TC-09-ATR-0003-IT' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0003_it' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0004-IP
-- Column attribute preservation: AUTO_INCREMENT
-- Type: TINYINT -> MEDIUMINT, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_09_atr_0004_ip, t2_tc_09_atr_0004_ip;
CREATE TABLE t1_tc_09_atr_0004_ip (
  id TINYINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0004_ip (id) VALUES (-128);
INSERT INTO t1_tc_09_atr_0004_ip (id) VALUES (127);
INSERT INTO t1_tc_09_atr_0004_ip (id) VALUES (-127);
INSERT INTO t1_tc_09_atr_0004_ip (id) VALUES (126);
INSERT INTO t1_tc_09_atr_0004_ip (id) VALUES (0);
ALTER TABLE t1_tc_09_atr_0004_ip MODIFY id MEDIUMINT NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_09_atr_0004_ip (id) VALUES (-8388608);
INSERT INTO t1_tc_09_atr_0004_ip (id) VALUES (-8388607);
INSERT INTO t1_tc_09_atr_0004_ip (id) VALUES (8388607);
SELECT 'TC-09-ATR-0004-IP' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0004_ip' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0005-IT
-- Column attribute preservation: AUTO_INCREMENT
-- Type: TINYINT -> INT, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_09_atr_0005_it, t2_tc_09_atr_0005_it;
CREATE TABLE t1_tc_09_atr_0005_it (
  id TINYINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0005_it (id) VALUES (-128);
INSERT INTO t1_tc_09_atr_0005_it (id) VALUES (127);
INSERT INTO t1_tc_09_atr_0005_it (id) VALUES (-127);
INSERT INTO t1_tc_09_atr_0005_it (id) VALUES (126);
INSERT INTO t1_tc_09_atr_0005_it (id) VALUES (0);
ALTER TABLE t1_tc_09_atr_0005_it MODIFY id INT NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_09_atr_0005_it (id) VALUES (-2147483648);
INSERT INTO t1_tc_09_atr_0005_it (id) VALUES (-2147483647);
INSERT INTO t1_tc_09_atr_0005_it (id) VALUES (2147483647);
SELECT 'TC-09-ATR-0005-IT' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0005_it' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0006-IP
-- Column attribute preservation: AUTO_INCREMENT
-- Type: TINYINT -> INT, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_09_atr_0006_ip, t2_tc_09_atr_0006_ip;
CREATE TABLE t1_tc_09_atr_0006_ip (
  id TINYINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0006_ip (id) VALUES (-128);
INSERT INTO t1_tc_09_atr_0006_ip (id) VALUES (127);
INSERT INTO t1_tc_09_atr_0006_ip (id) VALUES (-127);
INSERT INTO t1_tc_09_atr_0006_ip (id) VALUES (126);
INSERT INTO t1_tc_09_atr_0006_ip (id) VALUES (0);
ALTER TABLE t1_tc_09_atr_0006_ip MODIFY id INT NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_09_atr_0006_ip (id) VALUES (-2147483648);
INSERT INTO t1_tc_09_atr_0006_ip (id) VALUES (-2147483647);
INSERT INTO t1_tc_09_atr_0006_ip (id) VALUES (2147483647);
SELECT 'TC-09-ATR-0006-IP' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0006_ip' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0007-IT
-- Column attribute preservation: AUTO_INCREMENT
-- Type: TINYINT -> BIGINT, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_09_atr_0007_it, t2_tc_09_atr_0007_it;
CREATE TABLE t1_tc_09_atr_0007_it (
  id TINYINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0007_it (id) VALUES (-128);
INSERT INTO t1_tc_09_atr_0007_it (id) VALUES (127);
INSERT INTO t1_tc_09_atr_0007_it (id) VALUES (-127);
INSERT INTO t1_tc_09_atr_0007_it (id) VALUES (126);
INSERT INTO t1_tc_09_atr_0007_it (id) VALUES (0);
ALTER TABLE t1_tc_09_atr_0007_it MODIFY id BIGINT NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_09_atr_0007_it (id) VALUES (-9223372036854775808);
INSERT INTO t1_tc_09_atr_0007_it (id) VALUES (-9223372036854775807);
INSERT INTO t1_tc_09_atr_0007_it (id) VALUES (9223372036854775807);
SELECT 'TC-09-ATR-0007-IT' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0007_it' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0008-IP
-- Column attribute preservation: AUTO_INCREMENT
-- Type: TINYINT -> BIGINT, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_09_atr_0008_ip, t2_tc_09_atr_0008_ip;
CREATE TABLE t1_tc_09_atr_0008_ip (
  id TINYINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0008_ip (id) VALUES (-128);
INSERT INTO t1_tc_09_atr_0008_ip (id) VALUES (127);
INSERT INTO t1_tc_09_atr_0008_ip (id) VALUES (-127);
INSERT INTO t1_tc_09_atr_0008_ip (id) VALUES (126);
INSERT INTO t1_tc_09_atr_0008_ip (id) VALUES (0);
ALTER TABLE t1_tc_09_atr_0008_ip MODIFY id BIGINT NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_09_atr_0008_ip (id) VALUES (-9223372036854775808);
INSERT INTO t1_tc_09_atr_0008_ip (id) VALUES (-9223372036854775807);
INSERT INTO t1_tc_09_atr_0008_ip (id) VALUES (9223372036854775807);
SELECT 'TC-09-ATR-0008-IP' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0008_ip' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0009-IT
-- Column attribute preservation: AUTO_INCREMENT
-- Type: SMALLINT -> MEDIUMINT, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_09_atr_0009_it, t2_tc_09_atr_0009_it;
CREATE TABLE t1_tc_09_atr_0009_it (
  id SMALLINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0009_it (id) VALUES (-32768);
INSERT INTO t1_tc_09_atr_0009_it (id) VALUES (32767);
INSERT INTO t1_tc_09_atr_0009_it (id) VALUES (-32767);
INSERT INTO t1_tc_09_atr_0009_it (id) VALUES (32766);
INSERT INTO t1_tc_09_atr_0009_it (id) VALUES (0);
ALTER TABLE t1_tc_09_atr_0009_it MODIFY id MEDIUMINT NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_09_atr_0009_it (id) VALUES (-8388608);
INSERT INTO t1_tc_09_atr_0009_it (id) VALUES (-8388607);
INSERT INTO t1_tc_09_atr_0009_it (id) VALUES (8388607);
SELECT 'TC-09-ATR-0009-IT' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0009_it' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0010-IP
-- Column attribute preservation: AUTO_INCREMENT
-- Type: SMALLINT -> MEDIUMINT, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_09_atr_0010_ip, t2_tc_09_atr_0010_ip;
CREATE TABLE t1_tc_09_atr_0010_ip (
  id SMALLINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0010_ip (id) VALUES (-32768);
INSERT INTO t1_tc_09_atr_0010_ip (id) VALUES (32767);
INSERT INTO t1_tc_09_atr_0010_ip (id) VALUES (-32767);
INSERT INTO t1_tc_09_atr_0010_ip (id) VALUES (32766);
INSERT INTO t1_tc_09_atr_0010_ip (id) VALUES (0);
ALTER TABLE t1_tc_09_atr_0010_ip MODIFY id MEDIUMINT NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_09_atr_0010_ip (id) VALUES (-8388608);
INSERT INTO t1_tc_09_atr_0010_ip (id) VALUES (-8388607);
INSERT INTO t1_tc_09_atr_0010_ip (id) VALUES (8388607);
SELECT 'TC-09-ATR-0010-IP' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0010_ip' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0011-IT
-- Column attribute preservation: AUTO_INCREMENT
-- Type: SMALLINT -> INT, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_09_atr_0011_it, t2_tc_09_atr_0011_it;
CREATE TABLE t1_tc_09_atr_0011_it (
  id SMALLINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0011_it (id) VALUES (-32768);
INSERT INTO t1_tc_09_atr_0011_it (id) VALUES (32767);
INSERT INTO t1_tc_09_atr_0011_it (id) VALUES (-32767);
INSERT INTO t1_tc_09_atr_0011_it (id) VALUES (32766);
INSERT INTO t1_tc_09_atr_0011_it (id) VALUES (0);
ALTER TABLE t1_tc_09_atr_0011_it MODIFY id INT NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_09_atr_0011_it (id) VALUES (-2147483648);
INSERT INTO t1_tc_09_atr_0011_it (id) VALUES (-2147483647);
INSERT INTO t1_tc_09_atr_0011_it (id) VALUES (2147483647);
SELECT 'TC-09-ATR-0011-IT' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0011_it' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0012-IP
-- Column attribute preservation: AUTO_INCREMENT
-- Type: SMALLINT -> INT, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_09_atr_0012_ip, t2_tc_09_atr_0012_ip;
CREATE TABLE t1_tc_09_atr_0012_ip (
  id SMALLINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0012_ip (id) VALUES (-32768);
INSERT INTO t1_tc_09_atr_0012_ip (id) VALUES (32767);
INSERT INTO t1_tc_09_atr_0012_ip (id) VALUES (-32767);
INSERT INTO t1_tc_09_atr_0012_ip (id) VALUES (32766);
INSERT INTO t1_tc_09_atr_0012_ip (id) VALUES (0);
ALTER TABLE t1_tc_09_atr_0012_ip MODIFY id INT NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_09_atr_0012_ip (id) VALUES (-2147483648);
INSERT INTO t1_tc_09_atr_0012_ip (id) VALUES (-2147483647);
INSERT INTO t1_tc_09_atr_0012_ip (id) VALUES (2147483647);
SELECT 'TC-09-ATR-0012-IP' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0012_ip' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0013-IT
-- Column attribute preservation: AUTO_INCREMENT
-- Type: SMALLINT -> BIGINT, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_09_atr_0013_it, t2_tc_09_atr_0013_it;
CREATE TABLE t1_tc_09_atr_0013_it (
  id SMALLINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0013_it (id) VALUES (-32768);
INSERT INTO t1_tc_09_atr_0013_it (id) VALUES (32767);
INSERT INTO t1_tc_09_atr_0013_it (id) VALUES (-32767);
INSERT INTO t1_tc_09_atr_0013_it (id) VALUES (32766);
INSERT INTO t1_tc_09_atr_0013_it (id) VALUES (0);
ALTER TABLE t1_tc_09_atr_0013_it MODIFY id BIGINT NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_09_atr_0013_it (id) VALUES (-9223372036854775808);
INSERT INTO t1_tc_09_atr_0013_it (id) VALUES (-9223372036854775807);
INSERT INTO t1_tc_09_atr_0013_it (id) VALUES (9223372036854775807);
SELECT 'TC-09-ATR-0013-IT' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0013_it' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0014-IP
-- Column attribute preservation: AUTO_INCREMENT
-- Type: SMALLINT -> BIGINT, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_09_atr_0014_ip, t2_tc_09_atr_0014_ip;
CREATE TABLE t1_tc_09_atr_0014_ip (
  id SMALLINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0014_ip (id) VALUES (-32768);
INSERT INTO t1_tc_09_atr_0014_ip (id) VALUES (32767);
INSERT INTO t1_tc_09_atr_0014_ip (id) VALUES (-32767);
INSERT INTO t1_tc_09_atr_0014_ip (id) VALUES (32766);
INSERT INTO t1_tc_09_atr_0014_ip (id) VALUES (0);
ALTER TABLE t1_tc_09_atr_0014_ip MODIFY id BIGINT NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_09_atr_0014_ip (id) VALUES (-9223372036854775808);
INSERT INTO t1_tc_09_atr_0014_ip (id) VALUES (-9223372036854775807);
INSERT INTO t1_tc_09_atr_0014_ip (id) VALUES (9223372036854775807);
SELECT 'TC-09-ATR-0014-IP' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0014_ip' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0015-IT
-- Column attribute preservation: AUTO_INCREMENT
-- Type: MEDIUMINT -> INT, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_09_atr_0015_it, t2_tc_09_atr_0015_it;
CREATE TABLE t1_tc_09_atr_0015_it (
  id MEDIUMINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0015_it (id) VALUES (-8388608);
INSERT INTO t1_tc_09_atr_0015_it (id) VALUES (8388607);
INSERT INTO t1_tc_09_atr_0015_it (id) VALUES (-8388607);
INSERT INTO t1_tc_09_atr_0015_it (id) VALUES (8388606);
INSERT INTO t1_tc_09_atr_0015_it (id) VALUES (0);
ALTER TABLE t1_tc_09_atr_0015_it MODIFY id INT NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_09_atr_0015_it (id) VALUES (-2147483648);
INSERT INTO t1_tc_09_atr_0015_it (id) VALUES (-2147483647);
INSERT INTO t1_tc_09_atr_0015_it (id) VALUES (2147483647);
SELECT 'TC-09-ATR-0015-IT' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0015_it' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0016-IP
-- Column attribute preservation: AUTO_INCREMENT
-- Type: MEDIUMINT -> INT, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_09_atr_0016_ip, t2_tc_09_atr_0016_ip;
CREATE TABLE t1_tc_09_atr_0016_ip (
  id MEDIUMINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0016_ip (id) VALUES (-8388608);
INSERT INTO t1_tc_09_atr_0016_ip (id) VALUES (8388607);
INSERT INTO t1_tc_09_atr_0016_ip (id) VALUES (-8388607);
INSERT INTO t1_tc_09_atr_0016_ip (id) VALUES (8388606);
INSERT INTO t1_tc_09_atr_0016_ip (id) VALUES (0);
ALTER TABLE t1_tc_09_atr_0016_ip MODIFY id INT NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_09_atr_0016_ip (id) VALUES (-2147483648);
INSERT INTO t1_tc_09_atr_0016_ip (id) VALUES (-2147483647);
INSERT INTO t1_tc_09_atr_0016_ip (id) VALUES (2147483647);
SELECT 'TC-09-ATR-0016-IP' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0016_ip' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0017-IT
-- Column attribute preservation: AUTO_INCREMENT
-- Type: MEDIUMINT -> BIGINT, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_09_atr_0017_it, t2_tc_09_atr_0017_it;
CREATE TABLE t1_tc_09_atr_0017_it (
  id MEDIUMINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0017_it (id) VALUES (-8388608);
INSERT INTO t1_tc_09_atr_0017_it (id) VALUES (8388607);
INSERT INTO t1_tc_09_atr_0017_it (id) VALUES (-8388607);
INSERT INTO t1_tc_09_atr_0017_it (id) VALUES (8388606);
INSERT INTO t1_tc_09_atr_0017_it (id) VALUES (0);
ALTER TABLE t1_tc_09_atr_0017_it MODIFY id BIGINT NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_09_atr_0017_it (id) VALUES (-9223372036854775808);
INSERT INTO t1_tc_09_atr_0017_it (id) VALUES (-9223372036854775807);
INSERT INTO t1_tc_09_atr_0017_it (id) VALUES (9223372036854775807);
SELECT 'TC-09-ATR-0017-IT' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0017_it' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0018-IP
-- Column attribute preservation: AUTO_INCREMENT
-- Type: MEDIUMINT -> BIGINT, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_09_atr_0018_ip, t2_tc_09_atr_0018_ip;
CREATE TABLE t1_tc_09_atr_0018_ip (
  id MEDIUMINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0018_ip (id) VALUES (-8388608);
INSERT INTO t1_tc_09_atr_0018_ip (id) VALUES (8388607);
INSERT INTO t1_tc_09_atr_0018_ip (id) VALUES (-8388607);
INSERT INTO t1_tc_09_atr_0018_ip (id) VALUES (8388606);
INSERT INTO t1_tc_09_atr_0018_ip (id) VALUES (0);
ALTER TABLE t1_tc_09_atr_0018_ip MODIFY id BIGINT NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_09_atr_0018_ip (id) VALUES (-9223372036854775808);
INSERT INTO t1_tc_09_atr_0018_ip (id) VALUES (-9223372036854775807);
INSERT INTO t1_tc_09_atr_0018_ip (id) VALUES (9223372036854775807);
SELECT 'TC-09-ATR-0018-IP' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0018_ip' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0019-IT
-- Column attribute preservation: AUTO_INCREMENT
-- Type: INT -> BIGINT, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_09_atr_0019_it, t2_tc_09_atr_0019_it;
CREATE TABLE t1_tc_09_atr_0019_it (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0019_it (id) VALUES (-2147483648);
INSERT INTO t1_tc_09_atr_0019_it (id) VALUES (2147483647);
INSERT INTO t1_tc_09_atr_0019_it (id) VALUES (-2147483647);
INSERT INTO t1_tc_09_atr_0019_it (id) VALUES (2147483646);
INSERT INTO t1_tc_09_atr_0019_it (id) VALUES (0);
ALTER TABLE t1_tc_09_atr_0019_it MODIFY id BIGINT NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_09_atr_0019_it (id) VALUES (-9223372036854775808);
INSERT INTO t1_tc_09_atr_0019_it (id) VALUES (-9223372036854775807);
INSERT INTO t1_tc_09_atr_0019_it (id) VALUES (9223372036854775807);
SELECT 'TC-09-ATR-0019-IT' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0019_it' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0020-IP
-- Column attribute preservation: AUTO_INCREMENT
-- Type: INT -> BIGINT, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_09_atr_0020_ip, t2_tc_09_atr_0020_ip;
CREATE TABLE t1_tc_09_atr_0020_ip (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0020_ip (id) VALUES (-2147483648);
INSERT INTO t1_tc_09_atr_0020_ip (id) VALUES (2147483647);
INSERT INTO t1_tc_09_atr_0020_ip (id) VALUES (-2147483647);
INSERT INTO t1_tc_09_atr_0020_ip (id) VALUES (2147483646);
INSERT INTO t1_tc_09_atr_0020_ip (id) VALUES (0);
ALTER TABLE t1_tc_09_atr_0020_ip MODIFY id BIGINT NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_09_atr_0020_ip (id) VALUES (-9223372036854775808);
INSERT INTO t1_tc_09_atr_0020_ip (id) VALUES (-9223372036854775807);
INSERT INTO t1_tc_09_atr_0020_ip (id) VALUES (9223372036854775807);
SELECT 'TC-09-ATR-0020-IP' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0020_ip' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0021-IT
-- Column attribute preservation: AUTO_INCREMENT
-- Type: TINYINT UNSIGNED -> SMALLINT UNSIGNED, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_09_atr_0021_it, t2_tc_09_atr_0021_it;
CREATE TABLE t1_tc_09_atr_0021_it (
  id TINYINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0021_it (id) VALUES (0);
INSERT INTO t1_tc_09_atr_0021_it (id) VALUES (255);
INSERT INTO t1_tc_09_atr_0021_it (id) VALUES (254);
INSERT INTO t1_tc_09_atr_0021_it (id) VALUES (1);
INSERT INTO t1_tc_09_atr_0021_it (id) VALUES (42);
ALTER TABLE t1_tc_09_atr_0021_it MODIFY id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_09_atr_0021_it (id) VALUES (65535);
INSERT INTO t1_tc_09_atr_0021_it (id) VALUES (65534);
INSERT INTO t1_tc_09_atr_0021_it (id) VALUES (256);
SELECT 'TC-09-ATR-0021-IT' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0021_it' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0022-IP
-- Column attribute preservation: AUTO_INCREMENT
-- Type: TINYINT UNSIGNED -> SMALLINT UNSIGNED, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_09_atr_0022_ip, t2_tc_09_atr_0022_ip;
CREATE TABLE t1_tc_09_atr_0022_ip (
  id TINYINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0022_ip (id) VALUES (0);
INSERT INTO t1_tc_09_atr_0022_ip (id) VALUES (255);
INSERT INTO t1_tc_09_atr_0022_ip (id) VALUES (254);
INSERT INTO t1_tc_09_atr_0022_ip (id) VALUES (1);
INSERT INTO t1_tc_09_atr_0022_ip (id) VALUES (42);
ALTER TABLE t1_tc_09_atr_0022_ip MODIFY id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_09_atr_0022_ip (id) VALUES (65535);
INSERT INTO t1_tc_09_atr_0022_ip (id) VALUES (65534);
INSERT INTO t1_tc_09_atr_0022_ip (id) VALUES (256);
SELECT 'TC-09-ATR-0022-IP' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0022_ip' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0023-IT
-- Column attribute preservation: AUTO_INCREMENT
-- Type: TINYINT UNSIGNED -> MEDIUMINT UNSIGNED, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_09_atr_0023_it, t2_tc_09_atr_0023_it;
CREATE TABLE t1_tc_09_atr_0023_it (
  id TINYINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0023_it (id) VALUES (0);
INSERT INTO t1_tc_09_atr_0023_it (id) VALUES (255);
INSERT INTO t1_tc_09_atr_0023_it (id) VALUES (254);
INSERT INTO t1_tc_09_atr_0023_it (id) VALUES (1);
INSERT INTO t1_tc_09_atr_0023_it (id) VALUES (42);
ALTER TABLE t1_tc_09_atr_0023_it MODIFY id MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_09_atr_0023_it (id) VALUES (16777215);
INSERT INTO t1_tc_09_atr_0023_it (id) VALUES (16777214);
INSERT INTO t1_tc_09_atr_0023_it (id) VALUES (256);
SELECT 'TC-09-ATR-0023-IT' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0023_it' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0024-IP
-- Column attribute preservation: AUTO_INCREMENT
-- Type: TINYINT UNSIGNED -> MEDIUMINT UNSIGNED, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_09_atr_0024_ip, t2_tc_09_atr_0024_ip;
CREATE TABLE t1_tc_09_atr_0024_ip (
  id TINYINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0024_ip (id) VALUES (0);
INSERT INTO t1_tc_09_atr_0024_ip (id) VALUES (255);
INSERT INTO t1_tc_09_atr_0024_ip (id) VALUES (254);
INSERT INTO t1_tc_09_atr_0024_ip (id) VALUES (1);
INSERT INTO t1_tc_09_atr_0024_ip (id) VALUES (42);
ALTER TABLE t1_tc_09_atr_0024_ip MODIFY id MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_09_atr_0024_ip (id) VALUES (16777215);
INSERT INTO t1_tc_09_atr_0024_ip (id) VALUES (16777214);
INSERT INTO t1_tc_09_atr_0024_ip (id) VALUES (256);
SELECT 'TC-09-ATR-0024-IP' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0024_ip' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0025-IT
-- Column attribute preservation: AUTO_INCREMENT
-- Type: TINYINT UNSIGNED -> INT UNSIGNED, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_09_atr_0025_it, t2_tc_09_atr_0025_it;
CREATE TABLE t1_tc_09_atr_0025_it (
  id TINYINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0025_it (id) VALUES (0);
INSERT INTO t1_tc_09_atr_0025_it (id) VALUES (255);
INSERT INTO t1_tc_09_atr_0025_it (id) VALUES (254);
INSERT INTO t1_tc_09_atr_0025_it (id) VALUES (1);
INSERT INTO t1_tc_09_atr_0025_it (id) VALUES (42);
ALTER TABLE t1_tc_09_atr_0025_it MODIFY id INT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_09_atr_0025_it (id) VALUES (4294967295);
INSERT INTO t1_tc_09_atr_0025_it (id) VALUES (4294967294);
INSERT INTO t1_tc_09_atr_0025_it (id) VALUES (256);
SELECT 'TC-09-ATR-0025-IT' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0025_it' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0026-IP
-- Column attribute preservation: AUTO_INCREMENT
-- Type: TINYINT UNSIGNED -> INT UNSIGNED, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_09_atr_0026_ip, t2_tc_09_atr_0026_ip;
CREATE TABLE t1_tc_09_atr_0026_ip (
  id TINYINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0026_ip (id) VALUES (0);
INSERT INTO t1_tc_09_atr_0026_ip (id) VALUES (255);
INSERT INTO t1_tc_09_atr_0026_ip (id) VALUES (254);
INSERT INTO t1_tc_09_atr_0026_ip (id) VALUES (1);
INSERT INTO t1_tc_09_atr_0026_ip (id) VALUES (42);
ALTER TABLE t1_tc_09_atr_0026_ip MODIFY id INT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_09_atr_0026_ip (id) VALUES (4294967295);
INSERT INTO t1_tc_09_atr_0026_ip (id) VALUES (4294967294);
INSERT INTO t1_tc_09_atr_0026_ip (id) VALUES (256);
SELECT 'TC-09-ATR-0026-IP' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0026_ip' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0027-IT
-- Column attribute preservation: AUTO_INCREMENT
-- Type: TINYINT UNSIGNED -> BIGINT UNSIGNED, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_09_atr_0027_it, t2_tc_09_atr_0027_it;
CREATE TABLE t1_tc_09_atr_0027_it (
  id TINYINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0027_it (id) VALUES (0);
INSERT INTO t1_tc_09_atr_0027_it (id) VALUES (255);
INSERT INTO t1_tc_09_atr_0027_it (id) VALUES (254);
INSERT INTO t1_tc_09_atr_0027_it (id) VALUES (1);
INSERT INTO t1_tc_09_atr_0027_it (id) VALUES (42);
ALTER TABLE t1_tc_09_atr_0027_it MODIFY id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_09_atr_0027_it (id) VALUES (18446744073709551615);
INSERT INTO t1_tc_09_atr_0027_it (id) VALUES (18446744073709551614);
INSERT INTO t1_tc_09_atr_0027_it (id) VALUES (256);
SELECT 'TC-09-ATR-0027-IT' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0027_it' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0028-IP
-- Column attribute preservation: AUTO_INCREMENT
-- Type: TINYINT UNSIGNED -> BIGINT UNSIGNED, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_09_atr_0028_ip, t2_tc_09_atr_0028_ip;
CREATE TABLE t1_tc_09_atr_0028_ip (
  id TINYINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0028_ip (id) VALUES (0);
INSERT INTO t1_tc_09_atr_0028_ip (id) VALUES (255);
INSERT INTO t1_tc_09_atr_0028_ip (id) VALUES (254);
INSERT INTO t1_tc_09_atr_0028_ip (id) VALUES (1);
INSERT INTO t1_tc_09_atr_0028_ip (id) VALUES (42);
ALTER TABLE t1_tc_09_atr_0028_ip MODIFY id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_09_atr_0028_ip (id) VALUES (18446744073709551615);
INSERT INTO t1_tc_09_atr_0028_ip (id) VALUES (18446744073709551614);
INSERT INTO t1_tc_09_atr_0028_ip (id) VALUES (256);
SELECT 'TC-09-ATR-0028-IP' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0028_ip' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0029-IT
-- Column attribute preservation: AUTO_INCREMENT
-- Type: SMALLINT UNSIGNED -> MEDIUMINT UNSIGNED, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_09_atr_0029_it, t2_tc_09_atr_0029_it;
CREATE TABLE t1_tc_09_atr_0029_it (
  id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0029_it (id) VALUES (0);
INSERT INTO t1_tc_09_atr_0029_it (id) VALUES (65535);
INSERT INTO t1_tc_09_atr_0029_it (id) VALUES (65534);
INSERT INTO t1_tc_09_atr_0029_it (id) VALUES (1);
INSERT INTO t1_tc_09_atr_0029_it (id) VALUES (42);
ALTER TABLE t1_tc_09_atr_0029_it MODIFY id MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_09_atr_0029_it (id) VALUES (16777215);
INSERT INTO t1_tc_09_atr_0029_it (id) VALUES (16777214);
INSERT INTO t1_tc_09_atr_0029_it (id) VALUES (65536);
SELECT 'TC-09-ATR-0029-IT' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0029_it' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0030-IP
-- Column attribute preservation: AUTO_INCREMENT
-- Type: SMALLINT UNSIGNED -> MEDIUMINT UNSIGNED, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_09_atr_0030_ip, t2_tc_09_atr_0030_ip;
CREATE TABLE t1_tc_09_atr_0030_ip (
  id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0030_ip (id) VALUES (0);
INSERT INTO t1_tc_09_atr_0030_ip (id) VALUES (65535);
INSERT INTO t1_tc_09_atr_0030_ip (id) VALUES (65534);
INSERT INTO t1_tc_09_atr_0030_ip (id) VALUES (1);
INSERT INTO t1_tc_09_atr_0030_ip (id) VALUES (42);
ALTER TABLE t1_tc_09_atr_0030_ip MODIFY id MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_09_atr_0030_ip (id) VALUES (16777215);
INSERT INTO t1_tc_09_atr_0030_ip (id) VALUES (16777214);
INSERT INTO t1_tc_09_atr_0030_ip (id) VALUES (65536);
SELECT 'TC-09-ATR-0030-IP' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0030_ip' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0031-IT
-- Column attribute preservation: AUTO_INCREMENT
-- Type: SMALLINT UNSIGNED -> INT UNSIGNED, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_09_atr_0031_it, t2_tc_09_atr_0031_it;
CREATE TABLE t1_tc_09_atr_0031_it (
  id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0031_it (id) VALUES (0);
INSERT INTO t1_tc_09_atr_0031_it (id) VALUES (65535);
INSERT INTO t1_tc_09_atr_0031_it (id) VALUES (65534);
INSERT INTO t1_tc_09_atr_0031_it (id) VALUES (1);
INSERT INTO t1_tc_09_atr_0031_it (id) VALUES (42);
ALTER TABLE t1_tc_09_atr_0031_it MODIFY id INT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_09_atr_0031_it (id) VALUES (4294967295);
INSERT INTO t1_tc_09_atr_0031_it (id) VALUES (4294967294);
INSERT INTO t1_tc_09_atr_0031_it (id) VALUES (65536);
SELECT 'TC-09-ATR-0031-IT' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0031_it' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0032-IP
-- Column attribute preservation: AUTO_INCREMENT
-- Type: SMALLINT UNSIGNED -> INT UNSIGNED, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_09_atr_0032_ip, t2_tc_09_atr_0032_ip;
CREATE TABLE t1_tc_09_atr_0032_ip (
  id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0032_ip (id) VALUES (0);
INSERT INTO t1_tc_09_atr_0032_ip (id) VALUES (65535);
INSERT INTO t1_tc_09_atr_0032_ip (id) VALUES (65534);
INSERT INTO t1_tc_09_atr_0032_ip (id) VALUES (1);
INSERT INTO t1_tc_09_atr_0032_ip (id) VALUES (42);
ALTER TABLE t1_tc_09_atr_0032_ip MODIFY id INT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_09_atr_0032_ip (id) VALUES (4294967295);
INSERT INTO t1_tc_09_atr_0032_ip (id) VALUES (4294967294);
INSERT INTO t1_tc_09_atr_0032_ip (id) VALUES (65536);
SELECT 'TC-09-ATR-0032-IP' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0032_ip' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0033-IT
-- Column attribute preservation: AUTO_INCREMENT
-- Type: SMALLINT UNSIGNED -> BIGINT UNSIGNED, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_09_atr_0033_it, t2_tc_09_atr_0033_it;
CREATE TABLE t1_tc_09_atr_0033_it (
  id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0033_it (id) VALUES (0);
INSERT INTO t1_tc_09_atr_0033_it (id) VALUES (65535);
INSERT INTO t1_tc_09_atr_0033_it (id) VALUES (65534);
INSERT INTO t1_tc_09_atr_0033_it (id) VALUES (1);
INSERT INTO t1_tc_09_atr_0033_it (id) VALUES (42);
ALTER TABLE t1_tc_09_atr_0033_it MODIFY id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_09_atr_0033_it (id) VALUES (18446744073709551615);
INSERT INTO t1_tc_09_atr_0033_it (id) VALUES (18446744073709551614);
INSERT INTO t1_tc_09_atr_0033_it (id) VALUES (65536);
SELECT 'TC-09-ATR-0033-IT' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0033_it' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0034-IP
-- Column attribute preservation: AUTO_INCREMENT
-- Type: SMALLINT UNSIGNED -> BIGINT UNSIGNED, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_09_atr_0034_ip, t2_tc_09_atr_0034_ip;
CREATE TABLE t1_tc_09_atr_0034_ip (
  id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0034_ip (id) VALUES (0);
INSERT INTO t1_tc_09_atr_0034_ip (id) VALUES (65535);
INSERT INTO t1_tc_09_atr_0034_ip (id) VALUES (65534);
INSERT INTO t1_tc_09_atr_0034_ip (id) VALUES (1);
INSERT INTO t1_tc_09_atr_0034_ip (id) VALUES (42);
ALTER TABLE t1_tc_09_atr_0034_ip MODIFY id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_09_atr_0034_ip (id) VALUES (18446744073709551615);
INSERT INTO t1_tc_09_atr_0034_ip (id) VALUES (18446744073709551614);
INSERT INTO t1_tc_09_atr_0034_ip (id) VALUES (65536);
SELECT 'TC-09-ATR-0034-IP' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0034_ip' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0035-IT
-- Column attribute preservation: AUTO_INCREMENT
-- Type: MEDIUMINT UNSIGNED -> INT UNSIGNED, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_09_atr_0035_it, t2_tc_09_atr_0035_it;
CREATE TABLE t1_tc_09_atr_0035_it (
  id MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0035_it (id) VALUES (0);
INSERT INTO t1_tc_09_atr_0035_it (id) VALUES (16777215);
INSERT INTO t1_tc_09_atr_0035_it (id) VALUES (16777214);
INSERT INTO t1_tc_09_atr_0035_it (id) VALUES (1);
INSERT INTO t1_tc_09_atr_0035_it (id) VALUES (42);
ALTER TABLE t1_tc_09_atr_0035_it MODIFY id INT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_09_atr_0035_it (id) VALUES (4294967295);
INSERT INTO t1_tc_09_atr_0035_it (id) VALUES (4294967294);
INSERT INTO t1_tc_09_atr_0035_it (id) VALUES (16777216);
SELECT 'TC-09-ATR-0035-IT' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0035_it' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0036-IP
-- Column attribute preservation: AUTO_INCREMENT
-- Type: MEDIUMINT UNSIGNED -> INT UNSIGNED, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_09_atr_0036_ip, t2_tc_09_atr_0036_ip;
CREATE TABLE t1_tc_09_atr_0036_ip (
  id MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0036_ip (id) VALUES (0);
INSERT INTO t1_tc_09_atr_0036_ip (id) VALUES (16777215);
INSERT INTO t1_tc_09_atr_0036_ip (id) VALUES (16777214);
INSERT INTO t1_tc_09_atr_0036_ip (id) VALUES (1);
INSERT INTO t1_tc_09_atr_0036_ip (id) VALUES (42);
ALTER TABLE t1_tc_09_atr_0036_ip MODIFY id INT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_09_atr_0036_ip (id) VALUES (4294967295);
INSERT INTO t1_tc_09_atr_0036_ip (id) VALUES (4294967294);
INSERT INTO t1_tc_09_atr_0036_ip (id) VALUES (16777216);
SELECT 'TC-09-ATR-0036-IP' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0036_ip' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0037-IT
-- Column attribute preservation: AUTO_INCREMENT
-- Type: MEDIUMINT UNSIGNED -> BIGINT UNSIGNED, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_09_atr_0037_it, t2_tc_09_atr_0037_it;
CREATE TABLE t1_tc_09_atr_0037_it (
  id MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0037_it (id) VALUES (0);
INSERT INTO t1_tc_09_atr_0037_it (id) VALUES (16777215);
INSERT INTO t1_tc_09_atr_0037_it (id) VALUES (16777214);
INSERT INTO t1_tc_09_atr_0037_it (id) VALUES (1);
INSERT INTO t1_tc_09_atr_0037_it (id) VALUES (42);
ALTER TABLE t1_tc_09_atr_0037_it MODIFY id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_09_atr_0037_it (id) VALUES (18446744073709551615);
INSERT INTO t1_tc_09_atr_0037_it (id) VALUES (18446744073709551614);
INSERT INTO t1_tc_09_atr_0037_it (id) VALUES (16777216);
SELECT 'TC-09-ATR-0037-IT' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0037_it' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0038-IP
-- Column attribute preservation: AUTO_INCREMENT
-- Type: MEDIUMINT UNSIGNED -> BIGINT UNSIGNED, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_09_atr_0038_ip, t2_tc_09_atr_0038_ip;
CREATE TABLE t1_tc_09_atr_0038_ip (
  id MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0038_ip (id) VALUES (0);
INSERT INTO t1_tc_09_atr_0038_ip (id) VALUES (16777215);
INSERT INTO t1_tc_09_atr_0038_ip (id) VALUES (16777214);
INSERT INTO t1_tc_09_atr_0038_ip (id) VALUES (1);
INSERT INTO t1_tc_09_atr_0038_ip (id) VALUES (42);
ALTER TABLE t1_tc_09_atr_0038_ip MODIFY id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_09_atr_0038_ip (id) VALUES (18446744073709551615);
INSERT INTO t1_tc_09_atr_0038_ip (id) VALUES (18446744073709551614);
INSERT INTO t1_tc_09_atr_0038_ip (id) VALUES (16777216);
SELECT 'TC-09-ATR-0038-IP' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0038_ip' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0039-IT
-- Column attribute preservation: AUTO_INCREMENT
-- Type: INT UNSIGNED -> BIGINT UNSIGNED, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_09_atr_0039_it, t2_tc_09_atr_0039_it;
CREATE TABLE t1_tc_09_atr_0039_it (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0039_it (id) VALUES (0);
INSERT INTO t1_tc_09_atr_0039_it (id) VALUES (4294967295);
INSERT INTO t1_tc_09_atr_0039_it (id) VALUES (4294967294);
INSERT INTO t1_tc_09_atr_0039_it (id) VALUES (1);
INSERT INTO t1_tc_09_atr_0039_it (id) VALUES (42);
ALTER TABLE t1_tc_09_atr_0039_it MODIFY id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_09_atr_0039_it (id) VALUES (18446744073709551615);
INSERT INTO t1_tc_09_atr_0039_it (id) VALUES (18446744073709551614);
INSERT INTO t1_tc_09_atr_0039_it (id) VALUES (4294967296);
SELECT 'TC-09-ATR-0039-IT' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0039_it' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-09-ATR-0040-IP
-- Column attribute preservation: AUTO_INCREMENT
-- Type: INT UNSIGNED -> BIGINT UNSIGNED, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_09_atr_0040_ip, t2_tc_09_atr_0040_ip;
CREATE TABLE t1_tc_09_atr_0040_ip (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_09_atr_0040_ip (id) VALUES (0);
INSERT INTO t1_tc_09_atr_0040_ip (id) VALUES (4294967295);
INSERT INTO t1_tc_09_atr_0040_ip (id) VALUES (4294967294);
INSERT INTO t1_tc_09_atr_0040_ip (id) VALUES (1);
INSERT INTO t1_tc_09_atr_0040_ip (id) VALUES (42);
ALTER TABLE t1_tc_09_atr_0040_ip MODIFY id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_09_atr_0040_ip (id) VALUES (18446744073709551615);
INSERT INTO t1_tc_09_atr_0040_ip (id) VALUES (18446744073709551614);
INSERT INTO t1_tc_09_atr_0040_ip (id) VALUES (4294967296);
SELECT 'TC-09-ATR-0040-IP' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_09_atr_0040_ip' AND column_name='id' AND extra LIKE '%auto_increment%';

