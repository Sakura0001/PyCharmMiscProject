-- ============================================================
-- RDS MySQL DDL 秒级/在线修改列类型 测试套件 — 阿里云环境
-- 环境说明: 所有功能开关默认开启
-- 覆盖类型: 整数(SIGNED/UNSIGNED) + CHAR + VARCHAR
-- 覆盖算法: INSTANT + INPLACE
-- ============================================================
-- 本文件由 generate_test_sql.py 自动生成, 请勿手动修改
-- Suite-Revision: 8d806086fd8b   (生成器源码哈希; 时间戳见 results/generation_manifest.json)
-- 用例 ID 规则: TC-<文件号>-<作用域>-<序号>-<IT|IP>  —— 全局唯一
--   作用域 REG=普通表 OFAT/二元组, ATR=列属性保持, SPE=特殊模式,
--          FK=外键, PTK=分区(目标列是分区键), PNK=分区(目标列非分区键)
-- ============================================================

SET SESSION sql_mode = 'STRICT_TRANS_TABLES';
SET SESSION innodb_lock_wait_timeout = 50;

-- File 10: 特殊模式 (连续ALTER + 多列ALTER + 虚拟生成列)

-- Test Case: TC-10-SPE-0001-IT
-- Consecutive ALTER: TINYINT UNSIGNED -> SMALLINT UNSIGNED -> MEDIUMINT UNSIGNED -> INT UNSIGNED -> BIGINT UNSIGNED
-- Algorithm: instant
-- @expect alter=SUCCESS build=SUCCESS assertions=2 column_type=bigint unsigned alter_sha=de5c01470cc3 alter_sha=82b5be6a3a9c alter_sha=798924e52dd7 alter_sha=b1ca2e6808f5
DROP TABLE IF EXISTS t1_tc_10_spe_0001_it, t2_tc_10_spe_0001_it;
CREATE TABLE t1_tc_10_spe_0001_it (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target TINYINT UNSIGNED,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_10_spe_0001_it (target) VALUES (0);
INSERT INTO t1_tc_10_spe_0001_it (target) VALUES (1);
INSERT INTO t1_tc_10_spe_0001_it (target) VALUES (255);
-- Step 1: ALTER to SMALLINT UNSIGNED
ALTER TABLE t1_tc_10_spe_0001_it MODIFY target SMALLINT UNSIGNED, ALGORITHM=instant;
INSERT INTO t1_tc_10_spe_0001_it (target) VALUES (256);
INSERT INTO t1_tc_10_spe_0001_it (target) VALUES (65535);
-- Step 2: ALTER to MEDIUMINT UNSIGNED
ALTER TABLE t1_tc_10_spe_0001_it MODIFY target MEDIUMINT UNSIGNED, ALGORITHM=instant;
INSERT INTO t1_tc_10_spe_0001_it (target) VALUES (65536);
INSERT INTO t1_tc_10_spe_0001_it (target) VALUES (16777215);
-- Step 3: ALTER to INT UNSIGNED
ALTER TABLE t1_tc_10_spe_0001_it MODIFY target INT UNSIGNED, ALGORITHM=instant;
INSERT INTO t1_tc_10_spe_0001_it (target) VALUES (16777216);
INSERT INTO t1_tc_10_spe_0001_it (target) VALUES (4294967295);
-- Step 4: ALTER to BIGINT UNSIGNED
ALTER TABLE t1_tc_10_spe_0001_it MODIFY target BIGINT UNSIGNED, ALGORITHM=instant;
INSERT INTO t1_tc_10_spe_0001_it (target) VALUES (4294967296);
INSERT INTO t1_tc_10_spe_0001_it (target) VALUES (18446744073709551615);
-- Oracle table with final type BIGINT UNSIGNED
CREATE TABLE t2_tc_10_spe_0001_it (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target BIGINT UNSIGNED,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t2_tc_10_spe_0001_it (target) VALUES (0);
INSERT INTO t2_tc_10_spe_0001_it (target) VALUES (1);
INSERT INTO t2_tc_10_spe_0001_it (target) VALUES (255);
INSERT INTO t2_tc_10_spe_0001_it (target) VALUES (256);
INSERT INTO t2_tc_10_spe_0001_it (target) VALUES (65535);
INSERT INTO t2_tc_10_spe_0001_it (target) VALUES (65536);
INSERT INTO t2_tc_10_spe_0001_it (target) VALUES (16777215);
INSERT INTO t2_tc_10_spe_0001_it (target) VALUES (16777216);
INSERT INTO t2_tc_10_spe_0001_it (target) VALUES (4294967295);
INSERT INTO t2_tc_10_spe_0001_it (target) VALUES (4294967296);
INSERT INTO t2_tc_10_spe_0001_it (target) VALUES (18446744073709551615);
SELECT 'TC-10-SPE-0001-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_10_spe_0001_it
   WHERE id NOT IN (SELECT id FROM t2_tc_10_spe_0001_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_10_spe_0001_it
   WHERE id NOT IN (SELECT id FROM t1_tc_10_spe_0001_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_10_spe_0001_it a JOIN t2_tc_10_spe_0001_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-10-SPE-0001-IT#META' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='bigint unsigned'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=bigint unsigned nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_10_spe_0001_it' AND column_name='target';

-- Test Case: TC-10-SPE-0002-IP
-- Consecutive ALTER: TINYINT UNSIGNED -> SMALLINT UNSIGNED -> MEDIUMINT UNSIGNED -> INT UNSIGNED -> BIGINT UNSIGNED
-- Algorithm: inplace
-- @expect alter=SUCCESS build=SUCCESS assertions=2 column_type=bigint unsigned alter_sha=17ba3bee14ea alter_sha=c5b3a6fcb8b6 alter_sha=a69e69720b51 alter_sha=603a153a0352
DROP TABLE IF EXISTS t1_tc_10_spe_0002_ip, t2_tc_10_spe_0002_ip;
CREATE TABLE t1_tc_10_spe_0002_ip (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target TINYINT UNSIGNED,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_10_spe_0002_ip (target) VALUES (0);
INSERT INTO t1_tc_10_spe_0002_ip (target) VALUES (1);
INSERT INTO t1_tc_10_spe_0002_ip (target) VALUES (255);
-- Step 1: ALTER to SMALLINT UNSIGNED
ALTER TABLE t1_tc_10_spe_0002_ip MODIFY target SMALLINT UNSIGNED, ALGORITHM=inplace;
INSERT INTO t1_tc_10_spe_0002_ip (target) VALUES (256);
INSERT INTO t1_tc_10_spe_0002_ip (target) VALUES (65535);
-- Step 2: ALTER to MEDIUMINT UNSIGNED
ALTER TABLE t1_tc_10_spe_0002_ip MODIFY target MEDIUMINT UNSIGNED, ALGORITHM=inplace;
INSERT INTO t1_tc_10_spe_0002_ip (target) VALUES (65536);
INSERT INTO t1_tc_10_spe_0002_ip (target) VALUES (16777215);
-- Step 3: ALTER to INT UNSIGNED
ALTER TABLE t1_tc_10_spe_0002_ip MODIFY target INT UNSIGNED, ALGORITHM=inplace;
INSERT INTO t1_tc_10_spe_0002_ip (target) VALUES (16777216);
INSERT INTO t1_tc_10_spe_0002_ip (target) VALUES (4294967295);
-- Step 4: ALTER to BIGINT UNSIGNED
ALTER TABLE t1_tc_10_spe_0002_ip MODIFY target BIGINT UNSIGNED, ALGORITHM=inplace;
INSERT INTO t1_tc_10_spe_0002_ip (target) VALUES (4294967296);
INSERT INTO t1_tc_10_spe_0002_ip (target) VALUES (18446744073709551615);
-- Oracle table with final type BIGINT UNSIGNED
CREATE TABLE t2_tc_10_spe_0002_ip (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target BIGINT UNSIGNED,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t2_tc_10_spe_0002_ip (target) VALUES (0);
INSERT INTO t2_tc_10_spe_0002_ip (target) VALUES (1);
INSERT INTO t2_tc_10_spe_0002_ip (target) VALUES (255);
INSERT INTO t2_tc_10_spe_0002_ip (target) VALUES (256);
INSERT INTO t2_tc_10_spe_0002_ip (target) VALUES (65535);
INSERT INTO t2_tc_10_spe_0002_ip (target) VALUES (65536);
INSERT INTO t2_tc_10_spe_0002_ip (target) VALUES (16777215);
INSERT INTO t2_tc_10_spe_0002_ip (target) VALUES (16777216);
INSERT INTO t2_tc_10_spe_0002_ip (target) VALUES (4294967295);
INSERT INTO t2_tc_10_spe_0002_ip (target) VALUES (4294967296);
INSERT INTO t2_tc_10_spe_0002_ip (target) VALUES (18446744073709551615);
SELECT 'TC-10-SPE-0002-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_10_spe_0002_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_10_spe_0002_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_10_spe_0002_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_10_spe_0002_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_10_spe_0002_ip a JOIN t2_tc_10_spe_0002_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-10-SPE-0002-IP#META' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='bigint unsigned'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=bigint unsigned nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_10_spe_0002_ip' AND column_name='target';

-- Test Case: TC-10-SPE-0003-IT
-- Consecutive ALTER: TINYINT -> SMALLINT -> MEDIUMINT -> INT -> BIGINT
-- Algorithm: instant
-- @expect alter=SUCCESS build=SUCCESS assertions=2 column_type=bigint alter_sha=f088f2e8a8c6 alter_sha=614ab2835328 alter_sha=aa34d2997e70 alter_sha=514db64b9a44
DROP TABLE IF EXISTS t1_tc_10_spe_0003_it, t2_tc_10_spe_0003_it;
CREATE TABLE t1_tc_10_spe_0003_it (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target TINYINT,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_10_spe_0003_it (target) VALUES (-128);
INSERT INTO t1_tc_10_spe_0003_it (target) VALUES (0);
INSERT INTO t1_tc_10_spe_0003_it (target) VALUES (1);
INSERT INTO t1_tc_10_spe_0003_it (target) VALUES (127);
-- Step 1: ALTER to SMALLINT
ALTER TABLE t1_tc_10_spe_0003_it MODIFY target SMALLINT, ALGORITHM=instant;
INSERT INTO t1_tc_10_spe_0003_it (target) VALUES (128);
INSERT INTO t1_tc_10_spe_0003_it (target) VALUES (32767);
-- Step 2: ALTER to MEDIUMINT
ALTER TABLE t1_tc_10_spe_0003_it MODIFY target MEDIUMINT, ALGORITHM=instant;
INSERT INTO t1_tc_10_spe_0003_it (target) VALUES (32768);
INSERT INTO t1_tc_10_spe_0003_it (target) VALUES (8388607);
-- Step 3: ALTER to INT
ALTER TABLE t1_tc_10_spe_0003_it MODIFY target INT, ALGORITHM=instant;
INSERT INTO t1_tc_10_spe_0003_it (target) VALUES (8388608);
INSERT INTO t1_tc_10_spe_0003_it (target) VALUES (2147483647);
-- Step 4: ALTER to BIGINT
ALTER TABLE t1_tc_10_spe_0003_it MODIFY target BIGINT, ALGORITHM=instant;
INSERT INTO t1_tc_10_spe_0003_it (target) VALUES (2147483648);
INSERT INTO t1_tc_10_spe_0003_it (target) VALUES (9223372036854775807);
-- Oracle table with final type BIGINT
CREATE TABLE t2_tc_10_spe_0003_it (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target BIGINT,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t2_tc_10_spe_0003_it (target) VALUES (-128);
INSERT INTO t2_tc_10_spe_0003_it (target) VALUES (0);
INSERT INTO t2_tc_10_spe_0003_it (target) VALUES (1);
INSERT INTO t2_tc_10_spe_0003_it (target) VALUES (127);
INSERT INTO t2_tc_10_spe_0003_it (target) VALUES (128);
INSERT INTO t2_tc_10_spe_0003_it (target) VALUES (32767);
INSERT INTO t2_tc_10_spe_0003_it (target) VALUES (32768);
INSERT INTO t2_tc_10_spe_0003_it (target) VALUES (8388607);
INSERT INTO t2_tc_10_spe_0003_it (target) VALUES (8388608);
INSERT INTO t2_tc_10_spe_0003_it (target) VALUES (2147483647);
INSERT INTO t2_tc_10_spe_0003_it (target) VALUES (2147483648);
INSERT INTO t2_tc_10_spe_0003_it (target) VALUES (9223372036854775807);
SELECT 'TC-10-SPE-0003-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_10_spe_0003_it
   WHERE id NOT IN (SELECT id FROM t2_tc_10_spe_0003_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_10_spe_0003_it
   WHERE id NOT IN (SELECT id FROM t1_tc_10_spe_0003_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_10_spe_0003_it a JOIN t2_tc_10_spe_0003_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-10-SPE-0003-IT#META' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='bigint'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=bigint nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_10_spe_0003_it' AND column_name='target';

-- Test Case: TC-10-SPE-0004-IP
-- Consecutive ALTER: TINYINT -> SMALLINT -> MEDIUMINT -> INT -> BIGINT
-- Algorithm: inplace
-- @expect alter=SUCCESS build=SUCCESS assertions=2 column_type=bigint alter_sha=8aec13390723 alter_sha=3058f5ae45bc alter_sha=da13996994d9 alter_sha=5f30c93670e7
DROP TABLE IF EXISTS t1_tc_10_spe_0004_ip, t2_tc_10_spe_0004_ip;
CREATE TABLE t1_tc_10_spe_0004_ip (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target TINYINT,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_10_spe_0004_ip (target) VALUES (-128);
INSERT INTO t1_tc_10_spe_0004_ip (target) VALUES (0);
INSERT INTO t1_tc_10_spe_0004_ip (target) VALUES (1);
INSERT INTO t1_tc_10_spe_0004_ip (target) VALUES (127);
-- Step 1: ALTER to SMALLINT
ALTER TABLE t1_tc_10_spe_0004_ip MODIFY target SMALLINT, ALGORITHM=inplace;
INSERT INTO t1_tc_10_spe_0004_ip (target) VALUES (128);
INSERT INTO t1_tc_10_spe_0004_ip (target) VALUES (32767);
-- Step 2: ALTER to MEDIUMINT
ALTER TABLE t1_tc_10_spe_0004_ip MODIFY target MEDIUMINT, ALGORITHM=inplace;
INSERT INTO t1_tc_10_spe_0004_ip (target) VALUES (32768);
INSERT INTO t1_tc_10_spe_0004_ip (target) VALUES (8388607);
-- Step 3: ALTER to INT
ALTER TABLE t1_tc_10_spe_0004_ip MODIFY target INT, ALGORITHM=inplace;
INSERT INTO t1_tc_10_spe_0004_ip (target) VALUES (8388608);
INSERT INTO t1_tc_10_spe_0004_ip (target) VALUES (2147483647);
-- Step 4: ALTER to BIGINT
ALTER TABLE t1_tc_10_spe_0004_ip MODIFY target BIGINT, ALGORITHM=inplace;
INSERT INTO t1_tc_10_spe_0004_ip (target) VALUES (2147483648);
INSERT INTO t1_tc_10_spe_0004_ip (target) VALUES (9223372036854775807);
-- Oracle table with final type BIGINT
CREATE TABLE t2_tc_10_spe_0004_ip (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  target BIGINT,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t2_tc_10_spe_0004_ip (target) VALUES (-128);
INSERT INTO t2_tc_10_spe_0004_ip (target) VALUES (0);
INSERT INTO t2_tc_10_spe_0004_ip (target) VALUES (1);
INSERT INTO t2_tc_10_spe_0004_ip (target) VALUES (127);
INSERT INTO t2_tc_10_spe_0004_ip (target) VALUES (128);
INSERT INTO t2_tc_10_spe_0004_ip (target) VALUES (32767);
INSERT INTO t2_tc_10_spe_0004_ip (target) VALUES (32768);
INSERT INTO t2_tc_10_spe_0004_ip (target) VALUES (8388607);
INSERT INTO t2_tc_10_spe_0004_ip (target) VALUES (8388608);
INSERT INTO t2_tc_10_spe_0004_ip (target) VALUES (2147483647);
INSERT INTO t2_tc_10_spe_0004_ip (target) VALUES (2147483648);
INSERT INTO t2_tc_10_spe_0004_ip (target) VALUES (9223372036854775807);
SELECT 'TC-10-SPE-0004-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_10_spe_0004_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_10_spe_0004_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_10_spe_0004_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_10_spe_0004_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_10_spe_0004_ip a JOIN t2_tc_10_spe_0004_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.target <=> b.target AND a.pad <=> b.pad)
) AS mismatches;
SELECT 'TC-10-SPE-0004-IP#META' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='bigint'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=bigint nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_10_spe_0004_ip' AND column_name='target';

-- Test Case: TC-10-SPE-0005-IT
-- Multi-column ALTER, Algorithm: instant
-- @expect alter=SUCCESS build=SUCCESS assertions=4 alter_sha=c5e15823368c
DROP TABLE IF EXISTS t1_tc_10_spe_0005_it, t2_tc_10_spe_0005_it;
CREATE TABLE t1_tc_10_spe_0005_it (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  col_int INT,
  col_char CHAR(10) CHARACTER SET utf8mb4,
  col_varchar VARCHAR(50) CHARACTER SET utf8mb4
) ENGINE=InnoDB;
INSERT INTO t1_tc_10_spe_0005_it (col_int, col_char, col_varchar)
VALUES (42, 'hello', 'world');
ALTER TABLE t1_tc_10_spe_0005_it MODIFY col_int BIGINT, MODIFY col_char CHAR(20) CHARACTER SET utf8mb4, MODIFY col_varchar VARCHAR(100) CHARACTER SET utf8mb4, ALGORITHM=instant;
INSERT INTO t1_tc_10_spe_0005_it (col_int, col_char, col_varchar)
VALUES (2147483648, 'hello_world_long', 'extended_string');
CREATE TABLE t2_tc_10_spe_0005_it (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  col_int BIGINT,
  col_char CHAR(20) CHARACTER SET utf8mb4,
  col_varchar VARCHAR(100) CHARACTER SET utf8mb4
) ENGINE=InnoDB;
INSERT INTO t2_tc_10_spe_0005_it (col_int, col_char, col_varchar)
VALUES (42, 'hello', 'world');
INSERT INTO t2_tc_10_spe_0005_it (col_int, col_char, col_varchar)
VALUES (2147483648, 'hello_world_long', 'extended_string');
SELECT 'TC-10-SPE-0005-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_10_spe_0005_it
   WHERE id NOT IN (SELECT id FROM t2_tc_10_spe_0005_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_10_spe_0005_it
   WHERE id NOT IN (SELECT id FROM t1_tc_10_spe_0005_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_10_spe_0005_it a JOIN t2_tc_10_spe_0005_it b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.col_int <=> b.col_int AND a.col_char <=> b.col_char AND a.col_varchar <=> b.col_varchar)
) AS mismatches;
SELECT 'TC-10-SPE-0005-IT#META_COL_INT' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='bigint'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=bigint nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_10_spe_0005_it' AND column_name='col_int';
SELECT 'TC-10-SPE-0005-IT#META_COL_CHAR' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='char(20)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'utf8mb4')
          AND (MAX(collation_name) <=> 'utf8mb4_0900_ai_ci')
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=3,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=char(20) nullable=YES has_default=0 charset=utf8mb4 collation=utf8mb4_0900_ai_ci extra= pos=3]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_10_spe_0005_it' AND column_name='col_char';
SELECT 'TC-10-SPE-0005-IT#META_COL_VARCHAR' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(100)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'utf8mb4')
          AND (MAX(collation_name) <=> 'utf8mb4_0900_ai_ci')
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=4,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(100) nullable=YES has_default=0 charset=utf8mb4 collation=utf8mb4_0900_ai_ci extra= pos=4]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_10_spe_0005_it' AND column_name='col_varchar';

-- Test Case: TC-10-SPE-0006-IP
-- Multi-column ALTER, Algorithm: inplace
-- @expect alter=SUCCESS build=SUCCESS assertions=4 alter_sha=7da88b56e139
DROP TABLE IF EXISTS t1_tc_10_spe_0006_ip, t2_tc_10_spe_0006_ip;
CREATE TABLE t1_tc_10_spe_0006_ip (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  col_int INT,
  col_char CHAR(10) CHARACTER SET utf8mb4,
  col_varchar VARCHAR(50) CHARACTER SET utf8mb4
) ENGINE=InnoDB;
INSERT INTO t1_tc_10_spe_0006_ip (col_int, col_char, col_varchar)
VALUES (42, 'hello', 'world');
ALTER TABLE t1_tc_10_spe_0006_ip MODIFY col_int BIGINT, MODIFY col_char CHAR(20) CHARACTER SET utf8mb4, MODIFY col_varchar VARCHAR(100) CHARACTER SET utf8mb4, ALGORITHM=inplace;
INSERT INTO t1_tc_10_spe_0006_ip (col_int, col_char, col_varchar)
VALUES (2147483648, 'hello_world_long', 'extended_string');
CREATE TABLE t2_tc_10_spe_0006_ip (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  col_int BIGINT,
  col_char CHAR(20) CHARACTER SET utf8mb4,
  col_varchar VARCHAR(100) CHARACTER SET utf8mb4
) ENGINE=InnoDB;
INSERT INTO t2_tc_10_spe_0006_ip (col_int, col_char, col_varchar)
VALUES (42, 'hello', 'world');
INSERT INTO t2_tc_10_spe_0006_ip (col_int, col_char, col_varchar)
VALUES (2147483648, 'hello_world_long', 'extended_string');
SELECT 'TC-10-SPE-0006-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_10_spe_0006_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_10_spe_0006_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_10_spe_0006_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_10_spe_0006_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_10_spe_0006_ip a JOIN t2_tc_10_spe_0006_ip b ON a.id = b.id
   WHERE NOT (a.id <=> b.id AND a.col_int <=> b.col_int AND a.col_char <=> b.col_char AND a.col_varchar <=> b.col_varchar)
) AS mismatches;
SELECT 'TC-10-SPE-0006-IP#META_COL_INT' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='bigint'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=bigint nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_10_spe_0006_ip' AND column_name='col_int';
SELECT 'TC-10-SPE-0006-IP#META_COL_CHAR' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='char(20)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'utf8mb4')
          AND (MAX(collation_name) <=> 'utf8mb4_0900_ai_ci')
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=3,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=char(20) nullable=YES has_default=0 charset=utf8mb4 collation=utf8mb4_0900_ai_ci extra= pos=3]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_10_spe_0006_ip' AND column_name='col_char';
SELECT 'TC-10-SPE-0006-IP#META_COL_VARCHAR' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='varchar(100)'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> 'utf8mb4')
          AND (MAX(collation_name) <=> 'utf8mb4_0900_ai_ci')
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=4,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=varchar(100) nullable=YES has_default=0 charset=utf8mb4 collation=utf8mb4_0900_ai_ci extra= pos=4]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_10_spe_0006_ip' AND column_name='col_varchar';

-- Test Case: TC-10-SPE-0007-IT
-- Virtual generated column + function index, Algorithm: instant
-- @expect alter=SUCCESS build=SUCCESS assertions=2 alter_sha=1d294d9cf5a6 column_type=bigint
DROP TABLE IF EXISTS t1_tc_10_spe_0007_it, t2_tc_10_spe_0007_it;
CREATE TABLE t1_tc_10_spe_0007_it (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  base_col INT,
  vcol BIGINT AS (base_col * 2) VIRTUAL,
  INDEX idx_vcol (vcol)
) ENGINE=InnoDB;
INSERT INTO t1_tc_10_spe_0007_it (base_col) VALUES (0), (1), (-1), (2147483647), (42), (-42), (NULL);
-- ALTER base_col INT -> BIGINT, expected: SUCCESS
ALTER TABLE t1_tc_10_spe_0007_it MODIFY base_col BIGINT, ALGORITHM=instant;
INSERT INTO t1_tc_10_spe_0007_it (base_col) VALUES (2147483648), (4611686018427387903), (-4611686018427387904);
CREATE TABLE t2_tc_10_spe_0007_it (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  base_col BIGINT,
  vcol BIGINT AS (base_col * 2) VIRTUAL
) ENGINE=InnoDB;
INSERT INTO t2_tc_10_spe_0007_it (base_col) VALUES (0), (1), (-1), (2147483647), (42), (-42), (NULL);
INSERT INTO t2_tc_10_spe_0007_it (base_col) VALUES (2147483648), (4611686018427387903), (-4611686018427387904);
SELECT 'TC-10-SPE-0007-IT' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_10_spe_0007_it
   WHERE id NOT IN (SELECT id FROM t2_tc_10_spe_0007_it)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_10_spe_0007_it
   WHERE id NOT IN (SELECT id FROM t1_tc_10_spe_0007_it)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_10_spe_0007_it a JOIN t2_tc_10_spe_0007_it b ON a.id = b.id
   WHERE NOT (a.base_col <=> b.base_col)
) AS mismatches;
SELECT 'TC-10-SPE-0007-IT#META' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='bigint'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=bigint nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_10_spe_0007_it' AND column_name='base_col';

-- Test Case: TC-10-SPE-0008-IP
-- Virtual generated column + function index, Algorithm: inplace
-- @expect alter=SUCCESS build=SUCCESS assertions=2 alter_sha=00168f0d192d column_type=bigint
DROP TABLE IF EXISTS t1_tc_10_spe_0008_ip, t2_tc_10_spe_0008_ip;
CREATE TABLE t1_tc_10_spe_0008_ip (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  base_col INT,
  vcol BIGINT AS (base_col * 2) VIRTUAL,
  INDEX idx_vcol (vcol)
) ENGINE=InnoDB;
INSERT INTO t1_tc_10_spe_0008_ip (base_col) VALUES (0), (1), (-1), (2147483647), (42), (-42), (NULL);
-- ALTER base_col INT -> BIGINT, expected: SUCCESS
ALTER TABLE t1_tc_10_spe_0008_ip MODIFY base_col BIGINT, ALGORITHM=inplace;
INSERT INTO t1_tc_10_spe_0008_ip (base_col) VALUES (2147483648), (4611686018427387903), (-4611686018427387904);
CREATE TABLE t2_tc_10_spe_0008_ip (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  base_col BIGINT,
  vcol BIGINT AS (base_col * 2) VIRTUAL
) ENGINE=InnoDB;
INSERT INTO t2_tc_10_spe_0008_ip (base_col) VALUES (0), (1), (-1), (2147483647), (42), (-42), (NULL);
INSERT INTO t2_tc_10_spe_0008_ip (base_col) VALUES (2147483648), (4611686018427387903), (-4611686018427387904);
SELECT 'TC-10-SPE-0008-IP' AS test_id,
       IF(COUNT(*)=0,'PASS','FAIL') AS result,
       IF(COUNT(*)=0,'',GROUP_CONCAT(CONCAT(src,':id=',id) SEPARATOR '; ')) AS mismatch
FROM (
  SELECT 't1_extra' AS src, id FROM t1_tc_10_spe_0008_ip
   WHERE id NOT IN (SELECT id FROM t2_tc_10_spe_0008_ip)
  UNION ALL
  SELECT 't2_extra' AS src, id FROM t2_tc_10_spe_0008_ip
   WHERE id NOT IN (SELECT id FROM t1_tc_10_spe_0008_ip)
  UNION ALL
  SELECT 'data_mismatch' AS src, a.id FROM t1_tc_10_spe_0008_ip a JOIN t2_tc_10_spe_0008_ip b ON a.id = b.id
   WHERE NOT (a.base_col <=> b.base_col)
) AS mismatches;
SELECT 'TC-10-SPE-0008-IP#META' AS test_id,
       IF(COUNT(*)=1
          AND MAX(column_type)='bigint'
          AND MAX(is_nullable)='YES'
          AND ((MAX(column_default) IS NOT NULL) = 0)
          AND (MAX(character_set_name) <=> NULL)
          AND (MAX(collation_name) <=> NULL)
          AND (MAX(extra) <=> '')
          AND MAX(ordinal_position)=2,'PASS','FAIL') AS result,
       CONCAT('rows=',COUNT(*),
              ' actual[type=',IFNULL(MAX(column_type),'<missing>'),
                     ' nullable=',IFNULL(MAX(is_nullable),'<missing>'),
                     ' has_default=',(MAX(column_default) IS NOT NULL),
                     ' charset=',IFNULL(MAX(character_set_name),'NULL'),
                     ' collation=',IFNULL(MAX(collation_name),'NULL'),
                     ' extra=',IFNULL(MAX(extra),'NULL'),
                     ' pos=',IFNULL(MAX(ordinal_position),-1),']',
              ' want[type=bigint nullable=YES has_default=0 charset=NULL collation=NULL extra= pos=2]') AS mismatch
FROM information_schema.columns
WHERE table_schema=DATABASE() AND table_name='t1_tc_10_spe_0008_ip' AND column_name='base_col';

