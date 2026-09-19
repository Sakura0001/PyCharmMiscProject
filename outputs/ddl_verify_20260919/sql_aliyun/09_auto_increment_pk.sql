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

-- File 09: AUTO_INCREMENT PK 扩容专项

-- Test Case: TC-AII001
-- Column attribute preservation: AUTO_INCREMENT
-- Type: TINYINT -> SMALLINT, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aii001, t2_tc_aii001;
CREATE TABLE t1_tc_aii001 (
  id TINYINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii001 (id) VALUES (-128);
INSERT INTO t1_tc_aii001 (id) VALUES (127);
INSERT INTO t1_tc_aii001 (id) VALUES (-127);
INSERT INTO t1_tc_aii001 (id) VALUES (126);
INSERT INTO t1_tc_aii001 (id) VALUES (0);
ALTER TABLE t1_tc_aii001 MODIFY id SMALLINT NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_aii001 (id) VALUES (-32768);
INSERT INTO t1_tc_aii001 (id) VALUES (-32767);
INSERT INTO t1_tc_aii001 (id) VALUES (32767);
SELECT 'TC-AII001' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii001' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII002
-- Column attribute preservation: AUTO_INCREMENT
-- Type: TINYINT -> SMALLINT, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_aii002, t2_tc_aii002;
CREATE TABLE t1_tc_aii002 (
  id TINYINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii002 (id) VALUES (-128);
INSERT INTO t1_tc_aii002 (id) VALUES (127);
INSERT INTO t1_tc_aii002 (id) VALUES (-127);
INSERT INTO t1_tc_aii002 (id) VALUES (126);
INSERT INTO t1_tc_aii002 (id) VALUES (0);
ALTER TABLE t1_tc_aii002 MODIFY id SMALLINT NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_aii002 (id) VALUES (-32768);
INSERT INTO t1_tc_aii002 (id) VALUES (-32767);
INSERT INTO t1_tc_aii002 (id) VALUES (32767);
SELECT 'TC-AII002' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii002' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII003
-- Column attribute preservation: AUTO_INCREMENT
-- Type: TINYINT -> MEDIUMINT, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aii003, t2_tc_aii003;
CREATE TABLE t1_tc_aii003 (
  id TINYINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii003 (id) VALUES (-128);
INSERT INTO t1_tc_aii003 (id) VALUES (127);
INSERT INTO t1_tc_aii003 (id) VALUES (-127);
INSERT INTO t1_tc_aii003 (id) VALUES (126);
INSERT INTO t1_tc_aii003 (id) VALUES (0);
ALTER TABLE t1_tc_aii003 MODIFY id MEDIUMINT NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_aii003 (id) VALUES (-8388608);
INSERT INTO t1_tc_aii003 (id) VALUES (-8388607);
INSERT INTO t1_tc_aii003 (id) VALUES (8388607);
SELECT 'TC-AII003' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii003' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII004
-- Column attribute preservation: AUTO_INCREMENT
-- Type: TINYINT -> MEDIUMINT, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_aii004, t2_tc_aii004;
CREATE TABLE t1_tc_aii004 (
  id TINYINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii004 (id) VALUES (-128);
INSERT INTO t1_tc_aii004 (id) VALUES (127);
INSERT INTO t1_tc_aii004 (id) VALUES (-127);
INSERT INTO t1_tc_aii004 (id) VALUES (126);
INSERT INTO t1_tc_aii004 (id) VALUES (0);
ALTER TABLE t1_tc_aii004 MODIFY id MEDIUMINT NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_aii004 (id) VALUES (-8388608);
INSERT INTO t1_tc_aii004 (id) VALUES (-8388607);
INSERT INTO t1_tc_aii004 (id) VALUES (8388607);
SELECT 'TC-AII004' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii004' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII005
-- Column attribute preservation: AUTO_INCREMENT
-- Type: TINYINT -> INT, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aii005, t2_tc_aii005;
CREATE TABLE t1_tc_aii005 (
  id TINYINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii005 (id) VALUES (-128);
INSERT INTO t1_tc_aii005 (id) VALUES (127);
INSERT INTO t1_tc_aii005 (id) VALUES (-127);
INSERT INTO t1_tc_aii005 (id) VALUES (126);
INSERT INTO t1_tc_aii005 (id) VALUES (0);
ALTER TABLE t1_tc_aii005 MODIFY id INT NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_aii005 (id) VALUES (-2147483648);
INSERT INTO t1_tc_aii005 (id) VALUES (-2147483647);
INSERT INTO t1_tc_aii005 (id) VALUES (2147483647);
SELECT 'TC-AII005' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii005' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII006
-- Column attribute preservation: AUTO_INCREMENT
-- Type: TINYINT -> INT, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_aii006, t2_tc_aii006;
CREATE TABLE t1_tc_aii006 (
  id TINYINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii006 (id) VALUES (-128);
INSERT INTO t1_tc_aii006 (id) VALUES (127);
INSERT INTO t1_tc_aii006 (id) VALUES (-127);
INSERT INTO t1_tc_aii006 (id) VALUES (126);
INSERT INTO t1_tc_aii006 (id) VALUES (0);
ALTER TABLE t1_tc_aii006 MODIFY id INT NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_aii006 (id) VALUES (-2147483648);
INSERT INTO t1_tc_aii006 (id) VALUES (-2147483647);
INSERT INTO t1_tc_aii006 (id) VALUES (2147483647);
SELECT 'TC-AII006' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii006' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII007
-- Column attribute preservation: AUTO_INCREMENT
-- Type: TINYINT -> BIGINT, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aii007, t2_tc_aii007;
CREATE TABLE t1_tc_aii007 (
  id TINYINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii007 (id) VALUES (-128);
INSERT INTO t1_tc_aii007 (id) VALUES (127);
INSERT INTO t1_tc_aii007 (id) VALUES (-127);
INSERT INTO t1_tc_aii007 (id) VALUES (126);
INSERT INTO t1_tc_aii007 (id) VALUES (0);
ALTER TABLE t1_tc_aii007 MODIFY id BIGINT NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_aii007 (id) VALUES (-9223372036854775808);
INSERT INTO t1_tc_aii007 (id) VALUES (-9223372036854775807);
INSERT INTO t1_tc_aii007 (id) VALUES (9223372036854775807);
SELECT 'TC-AII007' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii007' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII008
-- Column attribute preservation: AUTO_INCREMENT
-- Type: TINYINT -> BIGINT, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_aii008, t2_tc_aii008;
CREATE TABLE t1_tc_aii008 (
  id TINYINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii008 (id) VALUES (-128);
INSERT INTO t1_tc_aii008 (id) VALUES (127);
INSERT INTO t1_tc_aii008 (id) VALUES (-127);
INSERT INTO t1_tc_aii008 (id) VALUES (126);
INSERT INTO t1_tc_aii008 (id) VALUES (0);
ALTER TABLE t1_tc_aii008 MODIFY id BIGINT NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_aii008 (id) VALUES (-9223372036854775808);
INSERT INTO t1_tc_aii008 (id) VALUES (-9223372036854775807);
INSERT INTO t1_tc_aii008 (id) VALUES (9223372036854775807);
SELECT 'TC-AII008' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii008' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII009
-- Column attribute preservation: AUTO_INCREMENT
-- Type: SMALLINT -> MEDIUMINT, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aii009, t2_tc_aii009;
CREATE TABLE t1_tc_aii009 (
  id SMALLINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii009 (id) VALUES (-32768);
INSERT INTO t1_tc_aii009 (id) VALUES (32767);
INSERT INTO t1_tc_aii009 (id) VALUES (-32767);
INSERT INTO t1_tc_aii009 (id) VALUES (32766);
INSERT INTO t1_tc_aii009 (id) VALUES (0);
ALTER TABLE t1_tc_aii009 MODIFY id MEDIUMINT NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_aii009 (id) VALUES (-8388608);
INSERT INTO t1_tc_aii009 (id) VALUES (-8388607);
INSERT INTO t1_tc_aii009 (id) VALUES (8388607);
SELECT 'TC-AII009' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii009' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII010
-- Column attribute preservation: AUTO_INCREMENT
-- Type: SMALLINT -> MEDIUMINT, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_aii010, t2_tc_aii010;
CREATE TABLE t1_tc_aii010 (
  id SMALLINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii010 (id) VALUES (-32768);
INSERT INTO t1_tc_aii010 (id) VALUES (32767);
INSERT INTO t1_tc_aii010 (id) VALUES (-32767);
INSERT INTO t1_tc_aii010 (id) VALUES (32766);
INSERT INTO t1_tc_aii010 (id) VALUES (0);
ALTER TABLE t1_tc_aii010 MODIFY id MEDIUMINT NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_aii010 (id) VALUES (-8388608);
INSERT INTO t1_tc_aii010 (id) VALUES (-8388607);
INSERT INTO t1_tc_aii010 (id) VALUES (8388607);
SELECT 'TC-AII010' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii010' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII011
-- Column attribute preservation: AUTO_INCREMENT
-- Type: SMALLINT -> INT, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aii011, t2_tc_aii011;
CREATE TABLE t1_tc_aii011 (
  id SMALLINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii011 (id) VALUES (-32768);
INSERT INTO t1_tc_aii011 (id) VALUES (32767);
INSERT INTO t1_tc_aii011 (id) VALUES (-32767);
INSERT INTO t1_tc_aii011 (id) VALUES (32766);
INSERT INTO t1_tc_aii011 (id) VALUES (0);
ALTER TABLE t1_tc_aii011 MODIFY id INT NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_aii011 (id) VALUES (-2147483648);
INSERT INTO t1_tc_aii011 (id) VALUES (-2147483647);
INSERT INTO t1_tc_aii011 (id) VALUES (2147483647);
SELECT 'TC-AII011' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii011' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII012
-- Column attribute preservation: AUTO_INCREMENT
-- Type: SMALLINT -> INT, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_aii012, t2_tc_aii012;
CREATE TABLE t1_tc_aii012 (
  id SMALLINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii012 (id) VALUES (-32768);
INSERT INTO t1_tc_aii012 (id) VALUES (32767);
INSERT INTO t1_tc_aii012 (id) VALUES (-32767);
INSERT INTO t1_tc_aii012 (id) VALUES (32766);
INSERT INTO t1_tc_aii012 (id) VALUES (0);
ALTER TABLE t1_tc_aii012 MODIFY id INT NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_aii012 (id) VALUES (-2147483648);
INSERT INTO t1_tc_aii012 (id) VALUES (-2147483647);
INSERT INTO t1_tc_aii012 (id) VALUES (2147483647);
SELECT 'TC-AII012' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii012' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII013
-- Column attribute preservation: AUTO_INCREMENT
-- Type: SMALLINT -> BIGINT, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aii013, t2_tc_aii013;
CREATE TABLE t1_tc_aii013 (
  id SMALLINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii013 (id) VALUES (-32768);
INSERT INTO t1_tc_aii013 (id) VALUES (32767);
INSERT INTO t1_tc_aii013 (id) VALUES (-32767);
INSERT INTO t1_tc_aii013 (id) VALUES (32766);
INSERT INTO t1_tc_aii013 (id) VALUES (0);
ALTER TABLE t1_tc_aii013 MODIFY id BIGINT NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_aii013 (id) VALUES (-9223372036854775808);
INSERT INTO t1_tc_aii013 (id) VALUES (-9223372036854775807);
INSERT INTO t1_tc_aii013 (id) VALUES (9223372036854775807);
SELECT 'TC-AII013' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii013' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII014
-- Column attribute preservation: AUTO_INCREMENT
-- Type: SMALLINT -> BIGINT, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_aii014, t2_tc_aii014;
CREATE TABLE t1_tc_aii014 (
  id SMALLINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii014 (id) VALUES (-32768);
INSERT INTO t1_tc_aii014 (id) VALUES (32767);
INSERT INTO t1_tc_aii014 (id) VALUES (-32767);
INSERT INTO t1_tc_aii014 (id) VALUES (32766);
INSERT INTO t1_tc_aii014 (id) VALUES (0);
ALTER TABLE t1_tc_aii014 MODIFY id BIGINT NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_aii014 (id) VALUES (-9223372036854775808);
INSERT INTO t1_tc_aii014 (id) VALUES (-9223372036854775807);
INSERT INTO t1_tc_aii014 (id) VALUES (9223372036854775807);
SELECT 'TC-AII014' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii014' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII015
-- Column attribute preservation: AUTO_INCREMENT
-- Type: MEDIUMINT -> INT, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aii015, t2_tc_aii015;
CREATE TABLE t1_tc_aii015 (
  id MEDIUMINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii015 (id) VALUES (-8388608);
INSERT INTO t1_tc_aii015 (id) VALUES (8388607);
INSERT INTO t1_tc_aii015 (id) VALUES (-8388607);
INSERT INTO t1_tc_aii015 (id) VALUES (8388606);
INSERT INTO t1_tc_aii015 (id) VALUES (0);
ALTER TABLE t1_tc_aii015 MODIFY id INT NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_aii015 (id) VALUES (-2147483648);
INSERT INTO t1_tc_aii015 (id) VALUES (-2147483647);
INSERT INTO t1_tc_aii015 (id) VALUES (2147483647);
SELECT 'TC-AII015' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii015' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII016
-- Column attribute preservation: AUTO_INCREMENT
-- Type: MEDIUMINT -> INT, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_aii016, t2_tc_aii016;
CREATE TABLE t1_tc_aii016 (
  id MEDIUMINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii016 (id) VALUES (-8388608);
INSERT INTO t1_tc_aii016 (id) VALUES (8388607);
INSERT INTO t1_tc_aii016 (id) VALUES (-8388607);
INSERT INTO t1_tc_aii016 (id) VALUES (8388606);
INSERT INTO t1_tc_aii016 (id) VALUES (0);
ALTER TABLE t1_tc_aii016 MODIFY id INT NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_aii016 (id) VALUES (-2147483648);
INSERT INTO t1_tc_aii016 (id) VALUES (-2147483647);
INSERT INTO t1_tc_aii016 (id) VALUES (2147483647);
SELECT 'TC-AII016' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii016' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII017
-- Column attribute preservation: AUTO_INCREMENT
-- Type: MEDIUMINT -> BIGINT, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aii017, t2_tc_aii017;
CREATE TABLE t1_tc_aii017 (
  id MEDIUMINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii017 (id) VALUES (-8388608);
INSERT INTO t1_tc_aii017 (id) VALUES (8388607);
INSERT INTO t1_tc_aii017 (id) VALUES (-8388607);
INSERT INTO t1_tc_aii017 (id) VALUES (8388606);
INSERT INTO t1_tc_aii017 (id) VALUES (0);
ALTER TABLE t1_tc_aii017 MODIFY id BIGINT NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_aii017 (id) VALUES (-9223372036854775808);
INSERT INTO t1_tc_aii017 (id) VALUES (-9223372036854775807);
INSERT INTO t1_tc_aii017 (id) VALUES (9223372036854775807);
SELECT 'TC-AII017' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii017' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII018
-- Column attribute preservation: AUTO_INCREMENT
-- Type: MEDIUMINT -> BIGINT, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_aii018, t2_tc_aii018;
CREATE TABLE t1_tc_aii018 (
  id MEDIUMINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii018 (id) VALUES (-8388608);
INSERT INTO t1_tc_aii018 (id) VALUES (8388607);
INSERT INTO t1_tc_aii018 (id) VALUES (-8388607);
INSERT INTO t1_tc_aii018 (id) VALUES (8388606);
INSERT INTO t1_tc_aii018 (id) VALUES (0);
ALTER TABLE t1_tc_aii018 MODIFY id BIGINT NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_aii018 (id) VALUES (-9223372036854775808);
INSERT INTO t1_tc_aii018 (id) VALUES (-9223372036854775807);
INSERT INTO t1_tc_aii018 (id) VALUES (9223372036854775807);
SELECT 'TC-AII018' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii018' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII019
-- Column attribute preservation: AUTO_INCREMENT
-- Type: INT -> BIGINT, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aii019, t2_tc_aii019;
CREATE TABLE t1_tc_aii019 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii019 (id) VALUES (-2147483648);
INSERT INTO t1_tc_aii019 (id) VALUES (2147483647);
INSERT INTO t1_tc_aii019 (id) VALUES (-2147483647);
INSERT INTO t1_tc_aii019 (id) VALUES (2147483646);
INSERT INTO t1_tc_aii019 (id) VALUES (0);
ALTER TABLE t1_tc_aii019 MODIFY id BIGINT NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_aii019 (id) VALUES (-9223372036854775808);
INSERT INTO t1_tc_aii019 (id) VALUES (-9223372036854775807);
INSERT INTO t1_tc_aii019 (id) VALUES (9223372036854775807);
SELECT 'TC-AII019' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii019' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII020
-- Column attribute preservation: AUTO_INCREMENT
-- Type: INT -> BIGINT, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_aii020, t2_tc_aii020;
CREATE TABLE t1_tc_aii020 (
  id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii020 (id) VALUES (-2147483648);
INSERT INTO t1_tc_aii020 (id) VALUES (2147483647);
INSERT INTO t1_tc_aii020 (id) VALUES (-2147483647);
INSERT INTO t1_tc_aii020 (id) VALUES (2147483646);
INSERT INTO t1_tc_aii020 (id) VALUES (0);
ALTER TABLE t1_tc_aii020 MODIFY id BIGINT NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_aii020 (id) VALUES (-9223372036854775808);
INSERT INTO t1_tc_aii020 (id) VALUES (-9223372036854775807);
INSERT INTO t1_tc_aii020 (id) VALUES (9223372036854775807);
SELECT 'TC-AII020' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii020' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII021
-- Column attribute preservation: AUTO_INCREMENT
-- Type: TINYINT UNSIGNED -> SMALLINT UNSIGNED, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aii021, t2_tc_aii021;
CREATE TABLE t1_tc_aii021 (
  id TINYINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii021 (id) VALUES (0);
INSERT INTO t1_tc_aii021 (id) VALUES (255);
INSERT INTO t1_tc_aii021 (id) VALUES (254);
INSERT INTO t1_tc_aii021 (id) VALUES (1);
INSERT INTO t1_tc_aii021 (id) VALUES (42);
ALTER TABLE t1_tc_aii021 MODIFY id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_aii021 (id) VALUES (65535);
INSERT INTO t1_tc_aii021 (id) VALUES (65534);
INSERT INTO t1_tc_aii021 (id) VALUES (256);
SELECT 'TC-AII021' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii021' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII022
-- Column attribute preservation: AUTO_INCREMENT
-- Type: TINYINT UNSIGNED -> SMALLINT UNSIGNED, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_aii022, t2_tc_aii022;
CREATE TABLE t1_tc_aii022 (
  id TINYINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii022 (id) VALUES (0);
INSERT INTO t1_tc_aii022 (id) VALUES (255);
INSERT INTO t1_tc_aii022 (id) VALUES (254);
INSERT INTO t1_tc_aii022 (id) VALUES (1);
INSERT INTO t1_tc_aii022 (id) VALUES (42);
ALTER TABLE t1_tc_aii022 MODIFY id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_aii022 (id) VALUES (65535);
INSERT INTO t1_tc_aii022 (id) VALUES (65534);
INSERT INTO t1_tc_aii022 (id) VALUES (256);
SELECT 'TC-AII022' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii022' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII023
-- Column attribute preservation: AUTO_INCREMENT
-- Type: TINYINT UNSIGNED -> MEDIUMINT UNSIGNED, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aii023, t2_tc_aii023;
CREATE TABLE t1_tc_aii023 (
  id TINYINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii023 (id) VALUES (0);
INSERT INTO t1_tc_aii023 (id) VALUES (255);
INSERT INTO t1_tc_aii023 (id) VALUES (254);
INSERT INTO t1_tc_aii023 (id) VALUES (1);
INSERT INTO t1_tc_aii023 (id) VALUES (42);
ALTER TABLE t1_tc_aii023 MODIFY id MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_aii023 (id) VALUES (16777215);
INSERT INTO t1_tc_aii023 (id) VALUES (16777214);
INSERT INTO t1_tc_aii023 (id) VALUES (256);
SELECT 'TC-AII023' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii023' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII024
-- Column attribute preservation: AUTO_INCREMENT
-- Type: TINYINT UNSIGNED -> MEDIUMINT UNSIGNED, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_aii024, t2_tc_aii024;
CREATE TABLE t1_tc_aii024 (
  id TINYINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii024 (id) VALUES (0);
INSERT INTO t1_tc_aii024 (id) VALUES (255);
INSERT INTO t1_tc_aii024 (id) VALUES (254);
INSERT INTO t1_tc_aii024 (id) VALUES (1);
INSERT INTO t1_tc_aii024 (id) VALUES (42);
ALTER TABLE t1_tc_aii024 MODIFY id MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_aii024 (id) VALUES (16777215);
INSERT INTO t1_tc_aii024 (id) VALUES (16777214);
INSERT INTO t1_tc_aii024 (id) VALUES (256);
SELECT 'TC-AII024' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii024' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII025
-- Column attribute preservation: AUTO_INCREMENT
-- Type: TINYINT UNSIGNED -> INT UNSIGNED, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aii025, t2_tc_aii025;
CREATE TABLE t1_tc_aii025 (
  id TINYINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii025 (id) VALUES (0);
INSERT INTO t1_tc_aii025 (id) VALUES (255);
INSERT INTO t1_tc_aii025 (id) VALUES (254);
INSERT INTO t1_tc_aii025 (id) VALUES (1);
INSERT INTO t1_tc_aii025 (id) VALUES (42);
ALTER TABLE t1_tc_aii025 MODIFY id INT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_aii025 (id) VALUES (4294967295);
INSERT INTO t1_tc_aii025 (id) VALUES (4294967294);
INSERT INTO t1_tc_aii025 (id) VALUES (256);
SELECT 'TC-AII025' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii025' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII026
-- Column attribute preservation: AUTO_INCREMENT
-- Type: TINYINT UNSIGNED -> INT UNSIGNED, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_aii026, t2_tc_aii026;
CREATE TABLE t1_tc_aii026 (
  id TINYINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii026 (id) VALUES (0);
INSERT INTO t1_tc_aii026 (id) VALUES (255);
INSERT INTO t1_tc_aii026 (id) VALUES (254);
INSERT INTO t1_tc_aii026 (id) VALUES (1);
INSERT INTO t1_tc_aii026 (id) VALUES (42);
ALTER TABLE t1_tc_aii026 MODIFY id INT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_aii026 (id) VALUES (4294967295);
INSERT INTO t1_tc_aii026 (id) VALUES (4294967294);
INSERT INTO t1_tc_aii026 (id) VALUES (256);
SELECT 'TC-AII026' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii026' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII027
-- Column attribute preservation: AUTO_INCREMENT
-- Type: TINYINT UNSIGNED -> BIGINT UNSIGNED, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aii027, t2_tc_aii027;
CREATE TABLE t1_tc_aii027 (
  id TINYINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii027 (id) VALUES (0);
INSERT INTO t1_tc_aii027 (id) VALUES (255);
INSERT INTO t1_tc_aii027 (id) VALUES (254);
INSERT INTO t1_tc_aii027 (id) VALUES (1);
INSERT INTO t1_tc_aii027 (id) VALUES (42);
ALTER TABLE t1_tc_aii027 MODIFY id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_aii027 (id) VALUES (18446744073709551615);
INSERT INTO t1_tc_aii027 (id) VALUES (18446744073709551614);
INSERT INTO t1_tc_aii027 (id) VALUES (256);
SELECT 'TC-AII027' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii027' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII028
-- Column attribute preservation: AUTO_INCREMENT
-- Type: TINYINT UNSIGNED -> BIGINT UNSIGNED, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_aii028, t2_tc_aii028;
CREATE TABLE t1_tc_aii028 (
  id TINYINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii028 (id) VALUES (0);
INSERT INTO t1_tc_aii028 (id) VALUES (255);
INSERT INTO t1_tc_aii028 (id) VALUES (254);
INSERT INTO t1_tc_aii028 (id) VALUES (1);
INSERT INTO t1_tc_aii028 (id) VALUES (42);
ALTER TABLE t1_tc_aii028 MODIFY id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_aii028 (id) VALUES (18446744073709551615);
INSERT INTO t1_tc_aii028 (id) VALUES (18446744073709551614);
INSERT INTO t1_tc_aii028 (id) VALUES (256);
SELECT 'TC-AII028' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii028' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII029
-- Column attribute preservation: AUTO_INCREMENT
-- Type: SMALLINT UNSIGNED -> MEDIUMINT UNSIGNED, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aii029, t2_tc_aii029;
CREATE TABLE t1_tc_aii029 (
  id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii029 (id) VALUES (0);
INSERT INTO t1_tc_aii029 (id) VALUES (65535);
INSERT INTO t1_tc_aii029 (id) VALUES (65534);
INSERT INTO t1_tc_aii029 (id) VALUES (1);
INSERT INTO t1_tc_aii029 (id) VALUES (42);
ALTER TABLE t1_tc_aii029 MODIFY id MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_aii029 (id) VALUES (16777215);
INSERT INTO t1_tc_aii029 (id) VALUES (16777214);
INSERT INTO t1_tc_aii029 (id) VALUES (65536);
SELECT 'TC-AII029' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii029' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII030
-- Column attribute preservation: AUTO_INCREMENT
-- Type: SMALLINT UNSIGNED -> MEDIUMINT UNSIGNED, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_aii030, t2_tc_aii030;
CREATE TABLE t1_tc_aii030 (
  id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii030 (id) VALUES (0);
INSERT INTO t1_tc_aii030 (id) VALUES (65535);
INSERT INTO t1_tc_aii030 (id) VALUES (65534);
INSERT INTO t1_tc_aii030 (id) VALUES (1);
INSERT INTO t1_tc_aii030 (id) VALUES (42);
ALTER TABLE t1_tc_aii030 MODIFY id MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_aii030 (id) VALUES (16777215);
INSERT INTO t1_tc_aii030 (id) VALUES (16777214);
INSERT INTO t1_tc_aii030 (id) VALUES (65536);
SELECT 'TC-AII030' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii030' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII031
-- Column attribute preservation: AUTO_INCREMENT
-- Type: SMALLINT UNSIGNED -> INT UNSIGNED, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aii031, t2_tc_aii031;
CREATE TABLE t1_tc_aii031 (
  id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii031 (id) VALUES (0);
INSERT INTO t1_tc_aii031 (id) VALUES (65535);
INSERT INTO t1_tc_aii031 (id) VALUES (65534);
INSERT INTO t1_tc_aii031 (id) VALUES (1);
INSERT INTO t1_tc_aii031 (id) VALUES (42);
ALTER TABLE t1_tc_aii031 MODIFY id INT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_aii031 (id) VALUES (4294967295);
INSERT INTO t1_tc_aii031 (id) VALUES (4294967294);
INSERT INTO t1_tc_aii031 (id) VALUES (65536);
SELECT 'TC-AII031' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii031' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII032
-- Column attribute preservation: AUTO_INCREMENT
-- Type: SMALLINT UNSIGNED -> INT UNSIGNED, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_aii032, t2_tc_aii032;
CREATE TABLE t1_tc_aii032 (
  id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii032 (id) VALUES (0);
INSERT INTO t1_tc_aii032 (id) VALUES (65535);
INSERT INTO t1_tc_aii032 (id) VALUES (65534);
INSERT INTO t1_tc_aii032 (id) VALUES (1);
INSERT INTO t1_tc_aii032 (id) VALUES (42);
ALTER TABLE t1_tc_aii032 MODIFY id INT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_aii032 (id) VALUES (4294967295);
INSERT INTO t1_tc_aii032 (id) VALUES (4294967294);
INSERT INTO t1_tc_aii032 (id) VALUES (65536);
SELECT 'TC-AII032' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii032' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII033
-- Column attribute preservation: AUTO_INCREMENT
-- Type: SMALLINT UNSIGNED -> BIGINT UNSIGNED, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aii033, t2_tc_aii033;
CREATE TABLE t1_tc_aii033 (
  id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii033 (id) VALUES (0);
INSERT INTO t1_tc_aii033 (id) VALUES (65535);
INSERT INTO t1_tc_aii033 (id) VALUES (65534);
INSERT INTO t1_tc_aii033 (id) VALUES (1);
INSERT INTO t1_tc_aii033 (id) VALUES (42);
ALTER TABLE t1_tc_aii033 MODIFY id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_aii033 (id) VALUES (18446744073709551615);
INSERT INTO t1_tc_aii033 (id) VALUES (18446744073709551614);
INSERT INTO t1_tc_aii033 (id) VALUES (65536);
SELECT 'TC-AII033' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii033' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII034
-- Column attribute preservation: AUTO_INCREMENT
-- Type: SMALLINT UNSIGNED -> BIGINT UNSIGNED, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_aii034, t2_tc_aii034;
CREATE TABLE t1_tc_aii034 (
  id SMALLINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii034 (id) VALUES (0);
INSERT INTO t1_tc_aii034 (id) VALUES (65535);
INSERT INTO t1_tc_aii034 (id) VALUES (65534);
INSERT INTO t1_tc_aii034 (id) VALUES (1);
INSERT INTO t1_tc_aii034 (id) VALUES (42);
ALTER TABLE t1_tc_aii034 MODIFY id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_aii034 (id) VALUES (18446744073709551615);
INSERT INTO t1_tc_aii034 (id) VALUES (18446744073709551614);
INSERT INTO t1_tc_aii034 (id) VALUES (65536);
SELECT 'TC-AII034' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii034' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII035
-- Column attribute preservation: AUTO_INCREMENT
-- Type: MEDIUMINT UNSIGNED -> INT UNSIGNED, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aii035, t2_tc_aii035;
CREATE TABLE t1_tc_aii035 (
  id MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii035 (id) VALUES (0);
INSERT INTO t1_tc_aii035 (id) VALUES (16777215);
INSERT INTO t1_tc_aii035 (id) VALUES (16777214);
INSERT INTO t1_tc_aii035 (id) VALUES (1);
INSERT INTO t1_tc_aii035 (id) VALUES (42);
ALTER TABLE t1_tc_aii035 MODIFY id INT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_aii035 (id) VALUES (4294967295);
INSERT INTO t1_tc_aii035 (id) VALUES (4294967294);
INSERT INTO t1_tc_aii035 (id) VALUES (16777216);
SELECT 'TC-AII035' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii035' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII036
-- Column attribute preservation: AUTO_INCREMENT
-- Type: MEDIUMINT UNSIGNED -> INT UNSIGNED, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_aii036, t2_tc_aii036;
CREATE TABLE t1_tc_aii036 (
  id MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii036 (id) VALUES (0);
INSERT INTO t1_tc_aii036 (id) VALUES (16777215);
INSERT INTO t1_tc_aii036 (id) VALUES (16777214);
INSERT INTO t1_tc_aii036 (id) VALUES (1);
INSERT INTO t1_tc_aii036 (id) VALUES (42);
ALTER TABLE t1_tc_aii036 MODIFY id INT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_aii036 (id) VALUES (4294967295);
INSERT INTO t1_tc_aii036 (id) VALUES (4294967294);
INSERT INTO t1_tc_aii036 (id) VALUES (16777216);
SELECT 'TC-AII036' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii036' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII037
-- Column attribute preservation: AUTO_INCREMENT
-- Type: MEDIUMINT UNSIGNED -> BIGINT UNSIGNED, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aii037, t2_tc_aii037;
CREATE TABLE t1_tc_aii037 (
  id MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii037 (id) VALUES (0);
INSERT INTO t1_tc_aii037 (id) VALUES (16777215);
INSERT INTO t1_tc_aii037 (id) VALUES (16777214);
INSERT INTO t1_tc_aii037 (id) VALUES (1);
INSERT INTO t1_tc_aii037 (id) VALUES (42);
ALTER TABLE t1_tc_aii037 MODIFY id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_aii037 (id) VALUES (18446744073709551615);
INSERT INTO t1_tc_aii037 (id) VALUES (18446744073709551614);
INSERT INTO t1_tc_aii037 (id) VALUES (16777216);
SELECT 'TC-AII037' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii037' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII038
-- Column attribute preservation: AUTO_INCREMENT
-- Type: MEDIUMINT UNSIGNED -> BIGINT UNSIGNED, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_aii038, t2_tc_aii038;
CREATE TABLE t1_tc_aii038 (
  id MEDIUMINT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii038 (id) VALUES (0);
INSERT INTO t1_tc_aii038 (id) VALUES (16777215);
INSERT INTO t1_tc_aii038 (id) VALUES (16777214);
INSERT INTO t1_tc_aii038 (id) VALUES (1);
INSERT INTO t1_tc_aii038 (id) VALUES (42);
ALTER TABLE t1_tc_aii038 MODIFY id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_aii038 (id) VALUES (18446744073709551615);
INSERT INTO t1_tc_aii038 (id) VALUES (18446744073709551614);
INSERT INTO t1_tc_aii038 (id) VALUES (16777216);
SELECT 'TC-AII038' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii038' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII039
-- Column attribute preservation: AUTO_INCREMENT
-- Type: INT UNSIGNED -> BIGINT UNSIGNED, Algorithm: instant
DROP TABLE IF EXISTS t1_tc_aii039, t2_tc_aii039;
CREATE TABLE t1_tc_aii039 (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii039 (id) VALUES (0);
INSERT INTO t1_tc_aii039 (id) VALUES (4294967295);
INSERT INTO t1_tc_aii039 (id) VALUES (4294967294);
INSERT INTO t1_tc_aii039 (id) VALUES (1);
INSERT INTO t1_tc_aii039 (id) VALUES (42);
ALTER TABLE t1_tc_aii039 MODIFY id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=instant;
INSERT INTO t1_tc_aii039 (id) VALUES (18446744073709551615);
INSERT INTO t1_tc_aii039 (id) VALUES (18446744073709551614);
INSERT INTO t1_tc_aii039 (id) VALUES (4294967296);
SELECT 'TC-AII039' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii039' AND column_name='id' AND extra LIKE '%auto_increment%';

-- Test Case: TC-AII040
-- Column attribute preservation: AUTO_INCREMENT
-- Type: INT UNSIGNED -> BIGINT UNSIGNED, Algorithm: inplace
DROP TABLE IF EXISTS t1_tc_aii040, t2_tc_aii040;
CREATE TABLE t1_tc_aii040 (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT PRIMARY KEY,
  pad VARCHAR(20) DEFAULT 'pad'
) ENGINE=InnoDB;
INSERT INTO t1_tc_aii040 (id) VALUES (0);
INSERT INTO t1_tc_aii040 (id) VALUES (4294967295);
INSERT INTO t1_tc_aii040 (id) VALUES (4294967294);
INSERT INTO t1_tc_aii040 (id) VALUES (1);
INSERT INTO t1_tc_aii040 (id) VALUES (42);
ALTER TABLE t1_tc_aii040 MODIFY id BIGINT UNSIGNED NOT NULL AUTO_INCREMENT, ALGORITHM=inplace;
INSERT INTO t1_tc_aii040 (id) VALUES (18446744073709551615);
INSERT INTO t1_tc_aii040 (id) VALUES (18446744073709551614);
INSERT INTO t1_tc_aii040 (id) VALUES (4294967296);
SELECT 'TC-AII040' AS test_id, IF(COUNT(*)>0,'PASS','FAIL') AS result FROM information_schema.columns WHERE table_name='t1_tc_aii040' AND column_name='id' AND extra LIKE '%auto_increment%';

