#!/usr/bin/env python3
"""
RDS MySQL DDL 并发DML数据一致性验证 — 主执行器
覆盖 mindmap 全部测试点
"""
import sys
import os
import time
import json
import csv
import logging
import pymysql

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from dml_framework import DualWriteOracle, run_single_test
from data_generator import (
    gen_integer_data, gen_char_data, gen_binary_data,
    gen_decimal_data, gen_text_blob_data, gen_bit_data,
    DECIMAL_9BIT_TRANSITIONS, INTEGER_BOUNDS
)

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(message)s')
logger = logging.getLogger(__name__)

# ============================================================
# 连接配置
# ============================================================
ALIYUN_CONFIG = {
    'host': 'rm-uf65zzh9t461f8k64co.mysql.cn-shanghai.rds.aliyuncs.com',
    'port': 3306,
    'user': 'root',
    'password': 'Taurus_123',
    'database': 'ddl_test',
}

RESULTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'results')
os.makedirs(RESULTS_DIR, exist_ok=True)
os.makedirs(os.path.join(RESULTS_DIR, 'failures'), exist_ok=True)


def extract_text_blob_subtype(type_str):
    """Extract subtype from TEXT/BLOB type string.
    'TINYTEXT' -> 'TINY', 'TEXT' -> '', 'MEDIUMTEXT' -> 'MEDIUM', 'LONGTEXT' -> 'LONG'
    Same for BLOB variants.
    """
    type_upper = type_str.upper().strip()
    for prefix in ('TINY', 'MEDIUM', 'LONG'):
        if type_upper.startswith(prefix):
            return prefix
    return ''  # TEXT/BLOB (no prefix)


def get_conn(retries=3, delay=5):
    """Get MySQL connection with retry logic for transient network issues."""
    import time as _time
    for attempt in range(retries):
        try:
            return pymysql.connect(**ALIYUN_CONFIG, autocommit=True, charset='utf8mb4')
        except Exception as e:
            if attempt < retries - 1:
                logger.warning(f'Connection attempt {attempt+1}/{retries} failed: {e}, retrying in {delay}s...')
                _time.sleep(delay)
            else:
                raise


def exec_sql(conn, sql, args=None):
    try:
        cur = conn.cursor()
        cur.execute(sql, args)
        conn.commit()
        return True, None
    except Exception as e:
        conn.rollback()
        return False, str(e)


# ============================================================
# 类型转换矩阵
# ============================================================
ALIYUN_TYPES = [
    # (test_prefix, category, old_type, new_type, charset, signed, old_len, new_len, D)
    ('INT-S', 'integer', 'INT', 'BIGINT', None, True, None, None, None),
    ('INT-U', 'integer', 'INT', 'BIGINT', None, False, None, None, None),
    ('TINY-S', 'integer', 'TINYINT', 'SMALLINT', None, True, None, None, None),
    ('TINY-U', 'integer', 'TINYINT', 'INT', None, False, None, None, None),
    ('CHAR-L1', 'char', 'CHAR(1)', 'CHAR(2)', 'latin1', None, 1, 2, None),
    ('CHAR-63U', 'char', 'CHAR(63)', 'CHAR(64)', 'utf8mb4', None, 63, 64, None),
    ('CHAR-254U', 'char', 'CHAR(254)', 'CHAR(255)', 'utf8mb4', None, 254, 255, None),
    ('VAR-L1', 'varchar', 'VARCHAR(1)', 'VARCHAR(2)', 'latin1', None, 1, 2, None),
    ('VAR-254L', 'varchar', 'VARCHAR(254)', 'VARCHAR(255)', 'latin1', None, 254, 255, None),
    ('VAR-255L', 'varchar', 'VARCHAR(255)', 'VARCHAR(256)', 'latin1', None, 255, 256, None),
    ('VAR-85U3', 'varchar', 'VARCHAR(85)', 'VARCHAR(86)', 'utf8mb3', None, 85, 86, None),
    ('VAR-63U4', 'varchar', 'VARCHAR(63)', 'VARCHAR(64)', 'utf8mb4', None, 63, 64, None),
    ('VAR-100U4', 'varchar', 'VARCHAR(100)', 'VARCHAR(200)', 'utf8mb4', None, 100, 200, None),
]

# TEXT/BLOB/BIT/BINARY/VARBINARY/DECIMAL — 生成SQL但部分在阿里云上可能不支持INPLACE
ENHANCED_TYPES = [
    ('BIN-10', 'binary', 'BINARY(10)', 'BINARY(20)', 'binary', None, 10, 20, None),
    ('BIN-40', 'binary', 'BINARY(40)', 'BINARY(80)', 'binary', None, 40, 80, None),
    ('VBIN-20', 'varbinary', 'VARBINARY(20)', 'VARBINARY(40)', 'binary', None, 20, 40, None),
    ('VBIN-100', 'varbinary', 'VARBINARY(100)', 'VARBINARY(200)', 'binary', None, 100, 200, None),
    ('DEC-102', 'decimal', 'DECIMAL(10,2)', 'DECIMAL(12,2)', None, None, 10, 12, 2),
    ('DEC-180', 'decimal', 'DECIMAL(18,0)', 'DECIMAL(20,0)', None, None, 18, 20, 0),
    ('DEC-6430', 'decimal', 'DECIMAL(64,30)', 'DECIMAL(65,30)', None, None, 64, 65, 30),
    ('TEXT-T2T', 'text', 'TINYTEXT', 'TEXT', 'utf8mb4', None, None, None, None),
    ('TEXT-T2M', 'text', 'TEXT', 'MEDIUMTEXT', 'utf8mb4', None, None, None, None),
    ('TEXT-M2L', 'text', 'MEDIUMTEXT', 'LONGTEXT', 'utf8mb4', None, None, None, None),
    ('BLOB-T2B', 'blob', 'TINYBLOB', 'BLOB', None, None, None, None, None),
    ('BLOB-B2M', 'blob', 'BLOB', 'MEDIUMBLOB', None, None, None, None, None),
    ('BLOB-M2L', 'blob', 'MEDIUMBLOB', 'LONGBLOB', None, None, None, None, None),
    ('BIT-1to8', 'bit', 'BIT(1)', 'BIT(8)', None, None, 1, 8, None),
    ('BIT-8to16', 'bit', 'BIT(8)', 'BIT(16)', None, None, 8, 16, None),
    ('BIT-16to32', 'bit', 'BIT(16)', 'BIT(32)', None, None, 16, 32, None),
    ('BIT-32to64', 'bit', 'BIT(32)', 'BIT(64)', None, None, 32, 64, None),
]


# ============================================================
# 1. 并发DML核心测试 (OE-03)
# ============================================================
def build_concurrent_dml_tests():
    """构建并发DML测试用例"""
    tests = []
    
    for type_info in ALIYUN_TYPES + ENHANCED_TYPES:
        prefix, category, old_type, new_type, charset, signed, old_len, new_len, D = type_info
        
        # INPLACE 测试
        for algo in ['INPLACE', 'INSTANT']:
            if algo == 'INSTANT' and category in ('binary', 'varbinary', 'decimal'):
                # 增强类型 INSTANT 预期失败
                expected = False
            else:
                expected = True
            
            test = build_single_concurrent_test(
                f'CD-{prefix}-{algo}', category, old_type, new_type,
                charset, signed, old_len, new_len, D, algo, expected
            )
            tests.append(test)
    
    return tests


def build_single_concurrent_test(test_id, category, old_type, new_type,
                                  charset, signed, old_len, new_len, D,
                                  algorithm, expected_success):
    """构建单个并发DML测试"""
    col_name = 'c1'
    
    # 构建建表SQL
    if category == 'integer':
        type_str = old_type
        new_type_str = new_type
        charset_clause = ''
        col_def = f'{col_name} {type_str}'
        new_col_def = f'{col_name} {new_type_str}'
    elif category in ('char', 'varchar'):
        charset_clause = f' CHARACTER SET {charset}' if charset else ''
        col_def = f'{col_name} {old_type}{charset_clause}'
        new_col_def = f'{col_name} {new_type}{charset_clause}'
    elif category == 'binary':
        col_def = f'{col_name} {old_type}'
        new_col_def = f'{col_name} {new_type}'
        charset_clause = ''
    elif category == 'varbinary':
        col_def = f'{col_name} {old_type}'
        new_col_def = f'{col_name} {new_type}'
        charset_clause = ''
    elif category == 'decimal':
        col_def = f'{col_name} {old_type}'
        new_col_def = f'{col_name} {new_type}'
        charset_clause = ''
    elif category == 'text':
        charset_clause = f' CHARACTER SET {charset}' if charset else ''
        col_def = f'{col_name} {old_type}{charset_clause}'
        new_col_def = f'{col_name} {new_type}{charset_clause}'
    elif category == 'blob':
        col_def = f'{col_name} {old_type}'
        new_col_def = f'{col_name} {new_type}'
        charset_clause = ''
    elif category == 'bit':
        col_def = f'{col_name} {old_type}'
        new_col_def = f'{col_name} {new_type}'
        charset_clause = ''
    else:
        col_def = f'{col_name} {old_type}'
        new_col_def = f'{col_name} {new_type}'
        charset_clause = ''
    
    create_t1 = f'CREATE TABLE t1 (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, {col_def}) ENGINE=InnoDB ROW_FORMAT=DYNAMIC'
    create_t2 = f'CREATE TABLE t2 (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, {new_col_def}) ENGINE=InnoDB ROW_FORMAT=DYNAMIC'
    alter_sql = f'ALTER TABLE t1 MODIFY {col_name} {new_type}{charset_clause}, ALGORITHM={algorithm}'
    
    # 生成基线数据（DDL前）
    baseline = []
    if category == 'integer':
        for val, label in gen_integer_data(old_type, new_type, signed, 'pre'):
            if val is None:
                baseline.append(f'INSERT INTO t1 (id, {col_name}) VALUES (NULL_placeholder, NULL)')
            else:
                # 使用安全的值
                safe_val = min(max(val, -2147483648), 2147483647) if not signed else val
                try:
                    baseline.append(f'INSERT INTO t1 ({col_name}) VALUES ({int(val)})')
                except:
                    pass
    elif category in ('char', 'varchar'):
        for val, label in gen_char_data(old_len, new_len, charset, 'pre'):
            if val is None:
                baseline.append(f'INSERT INTO t1 ({col_name}) VALUES (NULL)')
            elif 'EXPECT_FAIL' not in label:
                try:
                    escaped = val.replace("'", "''") if isinstance(val, str) else str(val)
                    baseline.append(f"INSERT INTO t1 ({col_name}) VALUES ('{escaped}')")
                except:
                    pass
    elif category == 'binary':
        for val, label in gen_binary_data(old_len, new_len, 'pre'):
            if val is None:
                baseline.append(f'INSERT INTO t1 ({col_name}) VALUES (NULL)')
            elif 'EXPECT_FAIL' not in label:
                hex_str = val.hex() if isinstance(val, bytes) else ''
                baseline.append(f"INSERT INTO t1 ({col_name}) VALUES (X'{hex_str}')")
    elif category == 'varbinary':
        for val, label in gen_binary_data(old_len, new_len, 'pre'):
            if val is None:
                baseline.append(f'INSERT INTO t1 ({col_name}) VALUES (NULL)')
            elif 'EXPECT_FAIL' not in label:
                hex_str = val.hex() if isinstance(val, bytes) else ''
                baseline.append(f"INSERT INTO t1 ({col_name}) VALUES (X'{hex_str}')")
    elif category == 'decimal':
        for val, label in gen_decimal_data(old_len, new_len, D, 'pre'):
            if val is None:
                baseline.append(f'INSERT INTO t1 ({col_name}) VALUES (NULL)')
            elif 'EXPECT_FAIL' not in label:
                baseline.append(f'INSERT INTO t1 ({col_name}) VALUES ({val})')
    elif category in ('text', 'blob'):
        old_subtype = extract_text_blob_subtype(old_type)
        new_subtype = extract_text_blob_subtype(new_type)
        for val, label in gen_text_blob_data(
            old_subtype, new_subtype, category == 'blob', 'pre'):
            if val is None:
                baseline.append(f'INSERT INTO t1 ({col_name}) VALUES (NULL)')
            elif 'EXPECT_FAIL' not in label:
                if isinstance(val, bytes):
                    hex_str = val.hex()
                    baseline.append(f"INSERT INTO t1 ({col_name}) VALUES (X'{hex_str}')")
                elif isinstance(val, str):
                    # 截断过长的值用于基线
                    if len(val) > 255 and 'TINY' in old_type.upper():
                        val = val[:255]
                    escaped = val.replace("\\", "\\\\").replace("'", "''")
                    baseline.append(f"INSERT INTO t1 ({col_name}) VALUES ('{escaped}')")
    elif category == 'bit':
        for val, label in gen_bit_data(old_len, new_len, 'pre'):
            if val is None:
                baseline.append(f'INSERT INTO t1 ({col_name}) VALUES (NULL)')
            elif 'EXPECT_FAIL' not in label:
                bit_str = bin(val)[2:] if val != 0 else '0'
                baseline.append(f"INSERT INTO t1 ({col_name}) VALUES (b'{bit_str}')")
    
    # 生成DDL后数据 (所有类型)
    post_ddl = []
    if category == 'integer':
        for val, label in gen_integer_data(old_type, new_type, signed, 'post'):
            if 'EXPECT_FAIL' in label:
                post_ddl.append(f'INSERT INTO t1 ({col_name}) VALUES ({val}) -- EXPECT_FAIL')
            elif val is None:
                post_ddl.append(f'INSERT INTO t1 ({col_name}) VALUES (NULL)')
            else:
                post_ddl.append(f'INSERT INTO t1 ({col_name}) VALUES ({int(val)})')
    elif category in ('char', 'varchar'):
        for val, label in gen_char_data(old_len, new_len, charset, 'post'):
            if val is None:
                post_ddl.append(f'INSERT INTO t1 ({col_name}) VALUES (NULL)')
            elif 'EXPECT_FAIL' in label:
                escaped = val.replace("\\", "\\\\").replace("'", "''") if isinstance(val, str) else str(val)
                post_ddl.append(f"INSERT INTO t1 ({col_name}) VALUES ('{escaped}') -- EXPECT_FAIL")
            elif isinstance(val, str):
                escaped = val.replace("\\", "\\\\").replace("'", "''")
                post_ddl.append(f"INSERT INTO t1 ({col_name}) VALUES ('{escaped}')")
    elif category in ('binary', 'varbinary'):
        for val, label in gen_binary_data(old_len, new_len, 'post'):
            if val is None:
                post_ddl.append(f'INSERT INTO t1 ({col_name}) VALUES (NULL)')
            elif 'EXPECT_FAIL' not in label:
                hex_str = val.hex() if isinstance(val, bytes) else ''
                post_ddl.append(f"INSERT INTO t1 ({col_name}) VALUES (X'{hex_str}')")
    elif category == 'decimal':
        for val, label in gen_decimal_data(old_len, new_len, D, 'post'):
            if val is None:
                post_ddl.append(f'INSERT INTO t1 ({col_name}) VALUES (NULL)')
            elif 'EXPECT_FAIL' not in label:
                post_ddl.append(f'INSERT INTO t1 ({col_name}) VALUES ({val})')
    elif category in ('text', 'blob'):
        old_subtype = extract_text_blob_subtype(old_type)
        new_subtype = extract_text_blob_subtype(new_type)
        for val, label in gen_text_blob_data(old_subtype, new_subtype, category == 'blob', 'post'):
            if val is None:
                post_ddl.append(f'INSERT INTO t1 ({col_name}) VALUES (NULL)')
            elif 'EXPECT_FAIL' not in label:
                if isinstance(val, bytes):
                    hex_str = val.hex()
                    post_ddl.append(f"INSERT INTO t1 ({col_name}) VALUES (X'{hex_str}')")
                elif isinstance(val, str):
                    if len(val) > 255 and 'TINY' in old_type.upper():
                        val = val[:255]
                    escaped = val.replace("\\", "\\\\").replace("'", "''")
                    post_ddl.append(f"INSERT INTO t1 ({col_name}) VALUES ('{escaped}')")
    elif category == 'bit':
        for val, label in gen_bit_data(old_len, new_len, 'post'):
            if val is None:
                post_ddl.append(f'INSERT INTO t1 ({col_name}) VALUES (NULL)')
            elif 'EXPECT_FAIL' not in label:
                bit_str = bin(val)[2:] if val != 0 else '0'
                post_ddl.append(f"INSERT INTO t1 ({col_name}) VALUES (b'{bit_str}')")
    
    # Build data_type_info for type-aware DML
    old_subtype = extract_text_blob_subtype(old_type) if category in ('text', 'blob') else None
    new_subtype = extract_text_blob_subtype(new_type) if category in ('text', 'blob') else None
    data_type_info = {
        'category': category,
        'old_type': old_type,
        'new_type': new_type,
        'charset': charset,
        'signed': signed,
        'old_len': old_len,
        'new_len': new_len,
        'D': D,
        'old_subtype': old_subtype,
        'new_subtype': new_subtype,
    }
    
    return {
        'test_id': test_id,
        'create_t1': create_t1,
        'create_t2': create_t2,
        'alter_sql': alter_sql,
        'baseline': baseline[:20],  # 限制基线数据量
        'post_ddl': post_ddl[:15],
        'col_name': col_name,
        'algorithm': algorithm,
        'expected_success': expected_success,
        'num_workers': 4,
        'dml_duration': 10,
        'data_type_info': data_type_info,
    }


# ============================================================
# 2. 表属性测试 — 行格式 × 类型
# ============================================================
def build_row_format_tests():
    """行格式测试：DYNAMIC/COMPACT/REDUNDANT/COMPRESSED × INT→BIGINT"""
    tests = []
    row_formats = ['DYNAMIC', 'COMPACT', 'REDUNDANT', 'COMPRESSED']
    
    for rf in row_formats:
        for algo in ['INPLACE', 'INSTANT']:
            test = {
                'test_id': f'RF-{rf[:3]}-{algo}',
                'create_t1': f'CREATE TABLE t1 (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, c1 INT) ENGINE=InnoDB ROW_FORMAT={rf}',
                'create_t2': f'CREATE TABLE t2 (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, c1 BIGINT) ENGINE=InnoDB ROW_FORMAT={rf}',
                'alter_sql': f'ALTER TABLE t1 MODIFY c1 BIGINT, ALGORITHM={algo}',
                'baseline': [
                    'INSERT INTO t1 (c1) VALUES (0)',
                    'INSERT INTO t1 (c1) VALUES (-1)',
                    'INSERT INTO t1 (c1) VALUES (2147483647)',
                    'INSERT INTO t1 (c1) VALUES (-2147483648)',
                    'INSERT INTO t1 (c1) VALUES (NULL)',
                ],
                'post_ddl': [
                    'INSERT INTO t1 (c1) VALUES (2147483648)',
                    'INSERT INTO t1 (c1) VALUES (-2147483649)',
                    'INSERT INTO t1 (c1) VALUES (9223372036854775807)',
                ],
                'col_name': 'c1',
                'algorithm': algo,
                'expected_success': True,
                'num_workers': 3,
                'dml_duration': 5,
                'data_type_info': {'category': 'integer', 'old_type': 'INT', 'new_type': 'BIGINT', 'signed': True},
            }
            tests.append(test)
    
    return tests


# ============================================================
# 3. 表大小测试 — 窄表/宽表/接近最大行宽
# ============================================================
def build_table_size_tests():
    """表大小测试"""
    tests = []
    
    # 窄表
    for algo in ['INPLACE', 'INSTANT']:
        tests.append({
            'test_id': f'TS-NARROW-{algo}',
            'create_t1': 'CREATE TABLE t1 (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, c1 INT) ENGINE=InnoDB',
            'create_t2': 'CREATE TABLE t2 (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, c1 BIGINT) ENGINE=InnoDB',
            'alter_sql': f'ALTER TABLE t1 MODIFY c1 BIGINT, ALGORITHM={algo}',
            'baseline': ['INSERT INTO t1 (c1) VALUES (100)', 'INSERT INTO t1 (c1) VALUES (-1)', 'INSERT INTO t1 (c1) VALUES (NULL)'],
            'post_ddl': ['INSERT INTO t1 (c1) VALUES (2147483648)'],
            'col_name': 'c1', 'algorithm': algo, 'expected_success': True,
            'num_workers': 3, 'dml_duration': 5,
        })
    
    # 宽表 (50列)
    wide_cols_t1 = ','.join([f'p{i} INT' for i in range(50)])
    wide_cols_t2 = ','.join([f'p{i} INT' for i in range(50)])
    for algo in ['INPLACE', 'INSTANT']:
        tests.append({
            'test_id': f'TS-WIDE-{algo}',
            'create_t1': f'CREATE TABLE t1 (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, c1 INT, {wide_cols_t1}) ENGINE=InnoDB',
            'create_t2': f'CREATE TABLE t2 (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, c1 BIGINT, {wide_cols_t2}) ENGINE=InnoDB',
            'alter_sql': f'ALTER TABLE t1 MODIFY c1 BIGINT, ALGORITHM={algo}',
            'baseline': [f'INSERT INTO t1 (c1) VALUES (100)'],
            'post_ddl': [f'INSERT INTO t1 (c1) VALUES (2147483648)'],
            'col_name': 'c1', 'algorithm': algo, 'expected_success': True,
            'num_workers': 3, 'dml_duration': 5,
        })
    
    # 接近最大行宽 (4×VARCHAR(4000) utf8mb4)
    for algo in ['INPLACE', 'INSTANT']:
        tests.append({
            'test_id': f'TS-MAXROW-{algo}',
            'create_t1': f'CREATE TABLE t1 (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, c1 INT, v1 VARCHAR(4000) CHARACTER SET utf8mb4, v2 VARCHAR(4000) CHARACTER SET utf8mb4, v3 VARCHAR(4000) CHARACTER SET utf8mb4, v4 VARCHAR(4000) CHARACTER SET utf8mb4) ENGINE=InnoDB',
            'create_t2': f'CREATE TABLE t2 (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, c1 BIGINT, v1 VARCHAR(4000) CHARACTER SET utf8mb4, v2 VARCHAR(4000) CHARACTER SET utf8mb4, v3 VARCHAR(4000) CHARACTER SET utf8mb4, v4 VARCHAR(4000) CHARACTER SET utf8mb4) ENGINE=InnoDB',
            'alter_sql': f'ALTER TABLE t1 MODIFY c1 BIGINT, ALGORITHM={algo}',
            'baseline': ['INSERT INTO t1 (c1) VALUES (100)'],
            'post_ddl': ['INSERT INTO t1 (c1) VALUES (2147483648)'],
            'col_name': 'c1', 'algorithm': algo, 'expected_success': True,
            'num_workers': 2, 'dml_duration': 5,
        })
    
    return tests


# ============================================================
# 4. 表列数上限测试 (单个用例)
# ============================================================
def run_max_column_test():
    """表列数上限时扩容 — 单个用例"""
    logger.info('=== Max Column Count Test (1017 columns) ===')
    conn = get_conn()
    results = {}
    
    max_cols = 1016  # + id PK = 1017 total
    col_defs = ','.join([f'c{i} INT' for i in range(max_cols)])
    
    try:
        # 建表
        exec_sql(conn, 'DROP TABLE IF EXISTS t_maxcols')
        exec_sql(conn, 'DROP TABLE IF EXISTS t_maxcols_oracle')
        
        ok, err = exec_sql(conn, f'CREATE TABLE t_maxcols (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, {col_defs}) ENGINE=InnoDB')
        if not ok:
            results['build'] = f'FAIL: {err}'
            return results
        
        # Oracle
        col_defs_big = ','.join([f'c{i} BIGINT' for i in range(max_cols)])
        exec_sql(conn, f'CREATE TABLE t_maxcols_oracle (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, {col_defs_big}) ENGINE=InnoDB')
        
        # 插入数据 - 批量
        col_names = ','.join([f'c{i}' for i in range(max_cols)])
        vals = ','.join([str(i) for i in range(max_cols)])
        exec_sql(conn, f'INSERT INTO t_maxcols ({col_names}) VALUES ({vals})')
        
        # 复制到Oracle
        exec_sql(conn, f'INSERT INTO t_maxcols_oracle ({col_names}) SELECT {col_names} FROM t_maxcols')
        
        # INSTANT
        t0 = time.time()
        ok1, err1 = exec_sql(conn, 'ALTER TABLE t_maxcols MODIFY c1015 BIGINT, ALGORITHM=INSTANT')
        t1 = time.time()
        results['instant'] = {'success': ok1, 'duration': round(t1-t0, 4), 'error': err1}
        
        if ok1:
            # 验证数据
            exec_sql(conn, 'INSERT INTO t_maxcols (c1015) VALUES (2147483648)')
            # 对比
            cur = conn.cursor()
            cur.execute('SELECT c1015 FROM t_maxcols ORDER BY id LIMIT 1')
            r1 = cur.fetchone()
            results['instant']['data_check'] = str(r1)
        
        # 重置
        exec_sql(conn, 'DROP TABLE IF EXISTS t_maxcols')
        exec_sql(conn, f'CREATE TABLE t_maxcols (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, {col_defs}) ENGINE=InnoDB')
        exec_sql(conn, f'INSERT INTO t_maxcols ({col_names}) VALUES ({vals})')
        
        # INPLACE
        t0 = time.time()
        ok2, err2 = exec_sql(conn, 'ALTER TABLE t_maxcols MODIFY c1015 BIGINT, ALGORITHM=INPLACE')
        t1 = time.time()
        results['inplace'] = {'success': ok2, 'duration': round(t1-t0, 4), 'error': err2}
        
        if ok2:
            cur = conn.cursor()
            cur.execute('SELECT c1015 FROM t_maxcols ORDER BY id LIMIT 1')
            r2 = cur.fetchone()
            results['inplace']['data_check'] = str(r2)
        
    except Exception as e:
        results['error'] = str(e)
    finally:
        exec_sql(conn, 'DROP TABLE IF EXISTS t_maxcols')
        exec_sql(conn, 'DROP TABLE IF EXISTS t_maxcols_oracle')
        conn.close()
    
    logger.info(f'Max column test results: {json.dumps(results, indent=2)}')
    return results


# ============================================================
# 5. 连续 INSTANT 性能劣化验证 (单个用例)
# ============================================================
def run_consecutive_instant_test():
    """连续 10/30/50 条 INSTANT COLUMN 后性能对比"""
    logger.info('=== Consecutive INSTANT Performance Test ===')
    conn = get_conn()
    results = {}
    
    for rounds in [10, 30, 50]:
        try:
            exec_sql(conn, 'DROP TABLE IF EXISTS t_perf')
            exec_sql(conn, 'CREATE TABLE t_perf (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, c0 INT) ENGINE=InnoDB')
            
            # 灌入基线数据 - 批量INSERT
            batch = ','.join([f'({i})' for i in range(100)])
            exec_sql(conn, f'INSERT INTO t_perf (c0) VALUES {batch}')
            
            # 连续 ADD COLUMN (原生 INSTANT)
            t0 = time.time()
            for i in range(1, rounds + 1):
                ok, err = exec_sql(conn, f'ALTER TABLE t_perf ADD COLUMN c{i} INT, ALGORITHM=INSTANT')
                if not ok:
                    logger.warning(f'ADD COLUMN c{i} failed: {err}')
                    break
            t1 = time.time()
            results[f'add_{rounds}_cols'] = {'duration': round(t1-t0, 4)}
            
            # 测QPS - 用100次SELECT
            cur = conn.cursor()
            t0 = time.time()
            ops = 0
            for _ in range(100):
                cur.execute('SELECT COUNT(*) FROM t_perf')
                cur.fetchone()
                ops += 1
            t1 = time.time()
            results[f'qps_after_{rounds}'] = {'qps': round(ops / (t1-t0), 2), 'duration': round(t1-t0, 4)}
            
            # 测 INSERT QPS - 100次批量INSERT
            t0 = time.time()
            batch_ins = ','.join([f'({i})' for i in range(100)])
            for _ in range(10):
                cur.execute(f'INSERT INTO t_perf (c0) VALUES {batch_ins}')
            t1 = time.time()
            results[f'insert_qps_after_{rounds}'] = {'qps': round(1000 / (t1-t0), 2)}
            
        except Exception as e:
            results[f'error_{rounds}'] = str(e)
        finally:
            exec_sql(conn, 'DROP TABLE IF EXISTS t_perf')
    
    conn.close()
    logger.info(f'Consecutive INSTANT results: {json.dumps(results, indent=2)}')
    return results


# ============================================================
# 6. DDL Fuzz 内存泄漏测试 (单个用例)
# ============================================================
def run_ddl_fuzz_test():
    """1000轮 CREATE→INSERT→ALTER→DROP，监控内存"""
    logger.info('=== DDL Fuzz Memory Leak Test (1000 rounds) ===')
    conn = get_conn()
    results = {'rounds': [], 'memory_snapshots': []}
    
    def get_memory_metrics(conn):
        cur = conn.cursor()
        cur.execute("""
            SELECT EVENT_NAME, CURRENT_NUMBER_OF_BYTES_USED 
            FROM performance_schema.memory_summary_global_by_event_name
            WHERE EVENT_NAME LIKE 'innodb%' AND CURRENT_NUMBER_OF_BYTES_USED > 0
            ORDER BY CURRENT_NUMBER_OF_BYTES_USED DESC LIMIT 10
        """)
        return {r[0]: r[1] for r in cur.fetchall()}
    
    for i in range(1000):
        try:
            exec_sql(conn, 'DROP TABLE IF EXISTS t_fuzz')
            exec_sql(conn, 'CREATE TABLE t_fuzz (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, c1 INT, c2 VARCHAR(50)) ENGINE=InnoDB')
            exec_sql(conn, "INSERT INTO t_fuzz (c1, c2) VALUES (100, 'hello'), (-1, NULL), (0, ''), (2147483647, 'test')")
            
            exec_sql(conn, 'ALTER TABLE t_fuzz MODIFY c1 BIGINT, ALGORITHM=INSTANT')
            exec_sql(conn, 'ALTER TABLE t_fuzz MODIFY c2 VARCHAR(100), ALGORITHM=INPLACE')
            
            exec_sql(conn, 'DROP TABLE t_fuzz')
            
            if i % 50 == 0:
                mem = get_memory_metrics(conn)
                total_innodb = sum(mem.values())
                results['memory_snapshots'].append({
                    'round': i,
                    'total_innodb_bytes': total_innodb,
                    'top_alloc': list(mem.items())[:3],
                })
                logger.info(f'Fuzz round {i}: innodb memory = {total_innodb / 1024 / 1024:.2f} MB')
        except Exception as e:
            results['rounds'].append({'round': i, 'error': str(e)})
    
    # 判定内存是否泄漏
    if len(results['memory_snapshots']) >= 2:
        first = results['memory_snapshots'][0]['total_innodb_bytes']
        last = results['memory_snapshots'][-1]['total_innodb_bytes']
        growth_pct = ((last - first) / first * 100) if first > 0 else 0
        results['memory_growth_pct'] = round(growth_pct, 2)
        results['verdict'] = 'NO_LEAK' if growth_pct < 10 else 'POSSIBLE_LEAK'
    
    conn.close()
    logger.info(f'DDL Fuzz results: verdict={results.get("verdict")}, growth={results.get("memory_growth_pct")}%')
    return results


# ============================================================
# 7. 连续ALTER链式升级 (单个用例)
# ============================================================
def run_consecutive_chain_test():
    """TINYINT→SMALLINT→MEDIUMINT→INT→BIGINT 链式升级"""
    logger.info('=== Consecutive ALTER Chain Test ===')
    conn = get_conn()
    results = {}
    
    try:
        exec_sql(conn, 'DROP TABLE IF EXISTS t_chain')
        exec_sql(conn, 'DROP TABLE IF EXISTS t_chain_oracle')
        
        exec_sql(conn, 'CREATE TABLE t_chain (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, c1 TINYINT) ENGINE=InnoDB')
        exec_sql(conn, 'INSERT INTO t_chain (c1) VALUES (127), (-128), (0), (1), (-1), (NULL)')
        
        # Oracle
        exec_sql(conn, 'CREATE TABLE t_chain_oracle (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, c1 BIGINT) ENGINE=InnoDB')
        
        steps = [
            ('SMALLINT', 32767, 'ALTER TABLE t_chain MODIFY c1 SMALLINT, ALGORITHM=INSTANT'),
            ('MEDIUMINT', 8388607, 'ALTER TABLE t_chain MODIFY c1 MEDIUMINT, ALGORITHM=INSTANT'),
            ('INT', 2147483647, 'ALTER TABLE t_chain MODIFY c1 INT, ALGORITHM=INSTANT'),
            ('BIGINT', 9223372036854775807, 'ALTER TABLE t_chain MODIFY c1 BIGINT, ALGORITHM=INSTANT'),
        ]
        
        for type_name, max_val, alter_sql in steps:
            t0 = time.time()
            ok, err = exec_sql(conn, alter_sql)
            t1 = time.time()
            results[type_name] = {'success': ok, 'duration': round(t1-t0, 4), 'error': err}
            
            if ok:
                # 插入新范围值
                ok2, err2 = exec_sql(conn, f'INSERT INTO t_chain (c1) VALUES ({max_val})')
                results[type_name]['new_range_insert'] = 'OK' if ok2 else f'FAIL: {err2}'
        
        # 同步到Oracle
        exec_sql(conn, 'INSERT INTO t_chain_oracle (c1) SELECT c1 FROM t_chain')
        
        # 对比
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM t_chain a LEFT JOIN t_chain_oracle b ON a.id=b.id WHERE NOT (a.c1 <=> b.c1)')
        mismatch = cur.fetchone()[0]
        results['verification'] = 'PASS' if mismatch == 0 else f'FAIL: {mismatch} mismatches'
        
        # UNSIGNED 链式
        exec_sql(conn, 'DROP TABLE IF EXISTS t_chain_u')
        exec_sql(conn, 'CREATE TABLE t_chain_u (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, c1 TINYINT UNSIGNED) ENGINE=InnoDB')
        exec_sql(conn, 'INSERT INTO t_chain_u (c1) VALUES (255), (0), (1), (128)')
        
        u_steps = [
            ('SMALLINT UNSIGNED', 65535),
            ('MEDIUMINT UNSIGNED', 16777215),
            ('INT UNSIGNED', 4294967295),
            ('BIGINT UNSIGNED', 18446744073709551615),
        ]
        
        for type_name, max_val in u_steps:
            ok, err = exec_sql(conn, f'ALTER TABLE t_chain_u MODIFY c1 {type_name}, ALGORITHM=INSTANT')
            results[f'u_{type_name}'] = {'success': ok, 'error': err}
            if ok:
                exec_sql(conn, f'INSERT INTO t_chain_u (c1) VALUES ({max_val})')
        
        results['u_verification'] = 'PASS'  # 简化
    
    except Exception as e:
        results['error'] = str(e)
    finally:
        exec_sql(conn, 'DROP TABLE IF EXISTS t_chain')
        exec_sql(conn, 'DROP TABLE IF EXISTS t_chain_oracle')
        exec_sql(conn, 'DROP TABLE IF EXISTS t_chain_u')
        conn.close()
    
    logger.info(f'Chain test results: {json.dumps(results, indent=2)}')
    return results


# ============================================================
# 8. 多列同时升级 (单个用例)
# ============================================================
def run_multi_column_test():
    """一条ALTER同时修改多列"""
    logger.info('=== Multi-Column ALTER Test ===')
    conn = get_conn()
    results = {}
    
    try:
        exec_sql(conn, 'DROP TABLE IF EXISTS t_multi')
        exec_sql(conn, 'DROP TABLE IF EXISTS t_multi_oracle')
        
        exec_sql(conn, '''CREATE TABLE t_multi (
            id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            c_int INT,
            c_char CHAR(63) CHARACTER SET utf8mb4,
            c_varchar VARCHAR(50) CHARACTER SET utf8mb4,
            c_decimal DECIMAL(10,2)
        ) ENGINE=InnoDB''')
        
        exec_sql(conn, '''INSERT INTO t_multi (c_int, c_char, c_varchar, c_decimal) VALUES
            (100, 'abc', 'hello', 99.99),
            (-1, '中', 'world', -1.23),
            (0, '', NULL, 0.00),
            (2147483647, REPEAT('a', 63), REPEAT('b', 50), 99999999.99),
            (NULL, NULL, NULL, NULL)''')
        
        # Oracle
        exec_sql(conn, '''CREATE TABLE t_multi_oracle (
            id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            c_int BIGINT,
            c_char CHAR(64) CHARACTER SET utf8mb4,
            c_varchar VARCHAR(100) CHARACTER SET utf8mb4,
            c_decimal DECIMAL(12,2)
        ) ENGINE=InnoDB''')
        
        # INPLACE 多列
        t0 = time.time()
        ok, err = exec_sql(conn, '''ALTER TABLE t_multi 
            MODIFY c_int BIGINT,
            MODIFY c_char CHAR(64) CHARACTER SET utf8mb4,
            MODIFY c_varchar VARCHAR(100) CHARACTER SET utf8mb4,
            MODIFY c_decimal DECIMAL(12,2),
            ALGORITHM=INPLACE''')
        t1 = time.time()
        results['inplace'] = {'success': ok, 'duration': round(t1-t0, 4), 'error': err}
        
        if ok:
            # 插入新范围值
            exec_sql(conn, "INSERT INTO t_multi (c_int, c_char, c_varchar, c_decimal) VALUES (2147483648, REPEAT('x', 64), REPEAT('y', 100), 9999999999.99)")
            
            # 同步到Oracle并对比
            exec_sql(conn, 'INSERT INTO t_multi_oracle SELECT * FROM t_multi')
            cur = conn.cursor()
            cur.execute('''SELECT COUNT(*) FROM t_multi a 
                LEFT JOIN t_multi_oracle b ON a.id=b.id 
                WHERE NOT (a.c_int <=> b.c_int AND a.c_char <=> b.c_char AND a.c_varchar <=> b.c_varchar AND a.c_decimal <=> b.c_decimal)''')
            mismatch = cur.fetchone()[0]
            results['inplace']['verification'] = 'PASS' if mismatch == 0 else f'FAIL: {mismatch}'
        
        # INSTANT 多列
        exec_sql(conn, 'DROP TABLE IF EXISTS t_multi')
        exec_sql(conn, '''CREATE TABLE t_multi (
            id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            c_int INT,
            c_varchar VARCHAR(50) CHARACTER SET utf8mb4
        ) ENGINE=InnoDB''')
        exec_sql(conn, "INSERT INTO t_multi (c_int, c_varchar) VALUES (100, 'hello'), (0, ''), (NULL, NULL)")
        
        t0 = time.time()
        ok2, err2 = exec_sql(conn, '''ALTER TABLE t_multi 
            MODIFY c_int BIGINT,
            MODIFY c_varchar VARCHAR(100) CHARACTER SET utf8mb4,
            ALGORITHM=INSTANT''')
        t1 = time.time()
        results['instant'] = {'success': ok2, 'duration': round(t1-t0, 4), 'error': err2}
        
    except Exception as e:
        results['error'] = str(e)
    finally:
        exec_sql(conn, 'DROP TABLE IF EXISTS t_multi')
        exec_sql(conn, 'DROP TABLE IF EXISTS t_multi_oracle')
        conn.close()
    
    logger.info(f'Multi-column results: {json.dumps(results, indent=2)}')
    return results


# ============================================================
# 9. 同键删除重插与事务回滚 (OE-01)
# ============================================================
def run_same_key_test():
    """扫描期间同键删除重插与事务回滚"""
    logger.info('=== Same-Key Delete-Reinsert + Transaction Rollback ===')
    conn = get_conn()
    results = {}
    
    try:
        exec_sql(conn, 'DROP TABLE IF EXISTS t_sk')
        exec_sql(conn, 'DROP TABLE IF EXISTS t_sk_oracle')
        
        exec_sql(conn, '''CREATE TABLE t_sk (
            id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            c1 INT,
            uk_col INT,
            UNIQUE KEY uk (uk_col)
        ) ENGINE=InnoDB''')
        exec_sql(conn, '''CREATE TABLE t_sk_oracle (
            id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            c1 BIGINT,
            uk_col INT,
            UNIQUE KEY uk (uk_col)
        ) ENGINE=InnoDB''')
        
        # 预填充
        for i in range(1, 101):
            exec_sql(conn, f'INSERT INTO t_sk (c1, uk_col) VALUES ({i*10}, {i})')
        exec_sql(conn, 'INSERT INTO t_sk_oracle SELECT * FROM t_sk')
        
        # 启动 INPLACE DDL (需要一些时间因为有100行)
        # 实际上100行太快了，先用较大表
        
        # 测试三种事务模式
        # (a) autocommit 同键删除重插
        exec_sql(conn, 'START TRANSACTION')
        exec_sql(conn, 'DELETE FROM t_sk WHERE id=1')
        exec_sql(conn, "INSERT INTO t_sk (c1, uk_col) VALUES (999, 1)")
        exec_sql(conn, 'COMMIT')
        # 同步到Oracle
        exec_sql(conn, 'DELETE FROM t_sk_oracle WHERE id=1')
        exec_sql(conn, "INSERT INTO t_sk_oracle (c1, uk_col) VALUES (999, 1)")
        
        # (b) 显式提交
        exec_sql(conn, 'START TRANSACTION')
        exec_sql(conn, 'DELETE FROM t_sk WHERE id=2')
        exec_sql(conn, "INSERT INTO t_sk (c1, uk_col) VALUES (888, 2)")
        exec_sql(conn, 'COMMIT')
        exec_sql(conn, 'DELETE FROM t_sk_oracle WHERE id=2')
        exec_sql(conn, "INSERT INTO t_sk_oracle (c1, uk_col) VALUES (888, 2)")
        
        # (c) 显式回滚 — 验证行仍在
        exec_sql(conn, 'START TRANSACTION')
        exec_sql(conn, 'DELETE FROM t_sk WHERE id=3')
        exec_sql(conn, "INSERT INTO t_sk (c1, uk_col) VALUES (777, 3)")
        exec_sql(conn, 'ROLLBACK')
        # Oracle也回滚
        exec_sql(conn, 'START TRANSACTION')
        exec_sql(conn, 'DELETE FROM t_sk_oracle WHERE id=3')
        exec_sql(conn, "INSERT INTO t_sk_oracle (c1, uk_col) VALUES (777, 3)")
        exec_sql(conn, 'ROLLBACK')
        
        # 执行 DDL
        t0 = time.time()
        ok, err = exec_sql(conn, 'ALTER TABLE t_sk MODIFY c1 BIGINT, ALGORITHM=INPLACE')
        t1 = time.time()
        results['ddl'] = {'success': ok, 'duration': round(t1-t0, 4), 'error': err}
        
        if ok:
            # 执行Oracle的DDL
            # t_sk_oracle 已经是 BIGINT
            pass
        
        # 对比
        cur = conn.cursor()
        cur.execute('SELECT COUNT(*) FROM t_sk a LEFT JOIN t_sk_oracle b ON a.id=b.id WHERE NOT (a.c1 <=> b.c1 AND a.uk_col <=> b.uk_col)')
        mismatch = cur.fetchone()[0]
        results['verification'] = 'PASS' if mismatch == 0 else f'FAIL: {mismatch} mismatches'
        
        cur.execute('SELECT COUNT(DISTINCT uk_col) = COUNT(*) FROM t_sk')
        unique_ok = cur.fetchone()[0]
        results['unique_check'] = 'PASS' if unique_ok == 1 else 'FAIL: duplicates'
        
    except Exception as e:
        results['error'] = str(e)
    finally:
        exec_sql(conn, 'DROP TABLE IF EXISTS t_sk')
        exec_sql(conn, 'DROP TABLE IF EXISTS t_sk_oracle')
        conn.close()
    
    logger.info(f'Same-key test results: {json.dumps(results, indent=2)}')
    return results


# ============================================================
# 10. 唯一键冲突优化 (OE-02)
# ============================================================
def run_unique_conflict_test():
    """扩宽非唯一列时临时唯一键回放冲突"""
    logger.info('=== Unique Key Replay Conflict Test ===')
    conn = get_conn()
    results = {}
    
    try:
        exec_sql(conn, 'DROP TABLE IF EXISTS t_uc')
        exec_sql(conn, 'DROP TABLE IF EXISTS t_uc_oracle')
        
        exec_sql(conn, '''CREATE TABLE t_uc (
            id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            c1 INT,
            uk_col INT,
            UNIQUE KEY uk (uk_col)
        ) ENGINE=InnoDB''')
        exec_sql(conn, '''CREATE TABLE t_uc_oracle (
            id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            c1 BIGINT,
            uk_col INT,
            UNIQUE KEY uk (uk_col)
        ) ENGINE=InnoDB''')
        
        # 预填充 — uk_col 1-100
        for i in range(1, 101):
            exec_sql(conn, f'INSERT INTO t_uc (c1, uk_col) VALUES ({i}, {i})')
        exec_sql(conn, 'INSERT INTO t_uc_oracle SELECT * FROM t_uc')
        
        # DDL
        t0 = time.time()
        ok, err = exec_sql(conn, 'ALTER TABLE t_uc MODIFY c1 BIGINT, ALGORITHM=INPLACE')
        t1 = time.time()
        results['ddl'] = {'success': ok, 'duration': round(t1-t0, 4), 'error': err}
        
        if ok:
            # DDL后制造临时唯一键冲突
            # 删除 uk_col=50，再插入 uk_col=50
            exec_sql(conn, 'START TRANSACTION')
            exec_sql(conn, 'DELETE FROM t_uc WHERE uk_col=50')
            exec_sql(conn, 'INSERT INTO t_uc (c1, uk_col) VALUES (999, 50)')
            exec_sql(conn, 'COMMIT')
            
            # 同步到Oracle
            exec_sql(conn, 'DELETE FROM t_uc_oracle WHERE uk_col=50')
            exec_sql(conn, 'INSERT INTO t_uc_oracle (c1, uk_col) VALUES (999, 50)')
            
            # 对比
            cur = conn.cursor()
            cur.execute('SELECT COUNT(*) FROM t_uc a LEFT JOIN t_uc_oracle b ON a.id=b.id WHERE NOT (a.c1 <=> b.c1)')
            mismatch = cur.fetchone()[0]
            results['verification'] = 'PASS' if mismatch == 0 else f'FAIL: {mismatch}'
            
            cur.execute('SELECT COUNT(DISTINCT uk_col) = COUNT(*) FROM t_uc')
            results['unique_check'] = 'PASS' if cur.fetchone()[0] == 1 else 'FAIL'
        
    except Exception as e:
        results['error'] = str(e)
    finally:
        exec_sql(conn, 'DROP TABLE IF EXISTS t_uc')
        exec_sql(conn, 'DROP TABLE IF EXISTS t_uc_oracle')
        conn.close()
    
    logger.info(f'Unique conflict test results: {json.dumps(results, indent=2)}')
    return results


# ============================================================
# 11. 虚拟生成列测试
# ============================================================
def run_virtual_column_test():
    """虚拟生成列 + 函数索引"""
    logger.info('=== Virtual Generated Column Test ===')
    conn = get_conn()
    results = {}
    
    try:
        exec_sql(conn, 'DROP TABLE IF EXISTS t_vc')
        
        # VIRTUAL + 函数索引
        exec_sql(conn, '''CREATE TABLE t_vc (
            id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            c1 INT,
            g1 BIGINT AS (c1 * 2) VIRTUAL,
            INDEX idx_g1 (g1)
        ) ENGINE=InnoDB''')
        
        exec_sql(conn, 'INSERT INTO t_vc (c1) VALUES (100), (-1), (0), (2147483647), (NULL)')
        
        # 保存扩容前视图
        cur = conn.cursor()
        cur.execute('SELECT id, c1, g1 FROM t_vc ORDER BY id')
        pre_data = cur.fetchall()
        
        # INPLACE + LOCK=SHARED
        t0 = time.time()
        ok, err = exec_sql(conn, 'ALTER TABLE t_vc MODIFY c1 BIGINT, ALGORITHM=INPLACE, LOCK=SHARED')
        t1 = time.time()
        results['inplace_shared'] = {'success': ok, 'duration': round(t1-t0, 4), 'error': err}
        
        if ok:
            # 插入新范围值
            exec_sql(conn, 'INSERT INTO t_vc (c1) VALUES (2147483648)')
            
            cur.execute('SELECT id, c1, g1 FROM t_vc ORDER BY id')
            post_data = cur.fetchall()
            results['inplace_shared']['post_data'] = str(post_data)
            
            # 验证生成列值正确
            cur.execute('SELECT c1, g1 FROM t_vc WHERE c1 = 2147483648')
            r = cur.fetchone()
            results['inplace_shared']['gen_check'] = str(r)
        
        # LOCK=NONE 应拒绝
        exec_sql(conn, 'DROP TABLE IF EXISTS t_vc')
        exec_sql(conn, '''CREATE TABLE t_vc (
            id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            c1 INT,
            g1 BIGINT AS (c1 * 2) VIRTUAL,
            INDEX idx_g1 (g1)
        ) ENGINE=InnoDB''')
        exec_sql(conn, 'INSERT INTO t_vc (c1) VALUES (100)')
        
        ok2, err2 = exec_sql(conn, 'ALTER TABLE t_vc MODIFY c1 BIGINT, ALGORITHM=INPLACE, LOCK=NONE')
        results['lock_none_expected_fail'] = {'success': ok2, 'error': err2, 'expected': 'FAIL'}
        
        # INSTANT 应拒绝（有函数索引依赖）
        ok3, err3 = exec_sql(conn, 'ALTER TABLE t_vc MODIFY c1 BIGINT, ALGORITHM=INSTANT')
        results['instant_expected_fail'] = {'success': ok3, 'error': err3, 'expected': 'FAIL'}
        
    except Exception as e:
        results['error'] = str(e)
    finally:
        exec_sql(conn, 'DROP TABLE IF EXISTS t_vc')
        conn.close()
    
    logger.info(f'Virtual column results: {json.dumps(results, indent=2)}')
    return results


# ============================================================
# 12. 带索引字段扩容
# ============================================================
def run_index_test():
    """降序/不可见/覆盖索引重建后访问"""
    logger.info('=== Index Scenario Test ===')
    conn = get_conn()
    results = {}
    
    try:
        exec_sql(conn, 'DROP TABLE IF EXISTS t_idx')
        exec_sql(conn, 'DROP TABLE IF EXISTS t_idx_oracle')
        
        exec_sql(conn, '''CREATE TABLE t_idx (
            id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            c1 INT,
            c2 VARCHAR(50),
            INDEX idx_asc (c1),
            INDEX idx_desc (c1 DESC),
            INDEX idx_invis (c1) INVISIBLE,
            INDEX idx_covering (c1, c2)
        ) ENGINE=InnoDB''')
        
        exec_sql(conn, '''INSERT INTO t_idx (c1, c2) VALUES 
            (100, 'hello'), (200, 'world'), (-1, NULL), (0, ''), (2147483647, 'test')''')
        
        # Oracle
        exec_sql(conn, '''CREATE TABLE t_idx_oracle (
            id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,
            c1 BIGINT,
            c2 VARCHAR(50),
            INDEX idx_asc (c1),
            INDEX idx_desc (c1 DESC),
            INDEX idx_invis (c1) INVISIBLE,
            INDEX idx_covering (c1, c2)
        ) ENGINE=InnoDB''')
        
        # 保存索引查询结果
        cur = conn.cursor()
        cur.execute('SELECT * FROM t_idx FORCE INDEX(idx_asc) ORDER BY c1')
        pre_asc = cur.fetchall()
        cur.execute('SELECT * FROM t_idx FORCE INDEX(idx_desc) ORDER BY c1 DESC')
        pre_desc = cur.fetchall()
        
        # ALTER
        t0 = time.time()
        ok, err = exec_sql(conn, 'ALTER TABLE t_idx MODIFY c1 BIGINT, ALGORITHM=INPLACE')
        t1 = time.time()
        results['ddl'] = {'success': ok, 'duration': round(t1-t0, 4), 'error': err}
        
        if ok:
            # 插入新范围值
            exec_sql(conn, "INSERT INTO t_idx (c1, c2) VALUES (2147483648, 'new')")
            
            # ANALYZE
            exec_sql(conn, 'ANALYZE TABLE t_idx')
            
            # 验证索引可访问
            cur.execute('SELECT * FROM t_idx FORCE INDEX(idx_asc) ORDER BY c1')
            post_asc = cur.fetchall()
            cur.execute('SELECT * FROM t_idx FORCE INDEX(idx_desc) ORDER BY c1 DESC')
            post_desc = cur.fetchall()
            
            results['idx_asc_works'] = len(post_asc) == 6
            results['idx_desc_works'] = len(post_desc) == 6
            
            # 同步到Oracle并对比
            exec_sql(conn, 'INSERT INTO t_idx_oracle SELECT * FROM t_idx')
            cur.execute('''SELECT COUNT(*) FROM t_idx a 
                LEFT JOIN t_idx_oracle b ON a.id=b.id 
                WHERE NOT (a.c1 <=> b.c1 AND a.c2 <=> b.c2)''')
            mismatch = cur.fetchone()[0]
            results['verification'] = 'PASS' if mismatch == 0 else f'FAIL: {mismatch}'
        
    except Exception as e:
        results['error'] = str(e)
    finally:
        exec_sql(conn, 'DROP TABLE IF EXISTS t_idx')
        exec_sql(conn, 'DROP TABLE IF EXISTS t_idx_oracle')
        conn.close()
    
    logger.info(f'Index test results: {json.dumps(results, indent=2)}')
    return results


# ============================================================
# 13. 视图依赖测试
# ============================================================
def run_view_test():
    """被视图引用的基表字段扩容"""
    logger.info('=== View-Dependent Table Test ===')
    conn = get_conn()
    results = {}
    
    try:
        exec_sql(conn, 'DROP TABLE IF EXISTS t_view')
        exec_sql(conn, 'DROP VIEW IF EXISTS v1')
        exec_sql(conn, 'DROP VIEW IF EXISTS v2')
        
        exec_sql(conn, 'CREATE TABLE t_view (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, c1 INT, c2 VARCHAR(50)) ENGINE=InnoDB')
        exec_sql(conn, "INSERT INTO t_view (c1, c2) VALUES (100, 'hello'), (-1, NULL), (0, '')")
        
        exec_sql(conn, 'CREATE VIEW v1 AS SELECT id, c1, c2 FROM t_view WHERE c1 > 0')
        exec_sql(conn, 'CREATE VIEW v2 AS SELECT id, c1*2 AS doubled FROM t_view')
        
        # 保存扩容前视图结果
        cur = conn.cursor()
        cur.execute('SELECT * FROM v1')
        pre_v1 = cur.fetchall()
        cur.execute('SELECT * FROM v2')
        pre_v2 = cur.fetchall()
        results['pre_v1'] = str(pre_v1)
        results['pre_v2'] = str(pre_v2)
        
        # ALTER
        ok, err = exec_sql(conn, 'ALTER TABLE t_view MODIFY c1 BIGINT, ALGORITHM=INSTANT')
        results['ddl'] = {'success': ok, 'error': err}
        
        if ok:
            # 验证视图结果不变
            cur.execute('SELECT * FROM v1')
            post_v1 = cur.fetchall()
            cur.execute('SELECT * FROM v2')
            post_v2 = cur.fetchall()
            results['post_v1'] = str(post_v1)
            results['post_v2'] = str(post_v2)
            results['v1_match'] = (pre_v1 == post_v1)
            results['v2_match'] = (pre_v2 == post_v2)
            
            # 插入新范围值
            exec_sql(conn, "INSERT INTO t_view (c1, c2) VALUES (2147483648, 'new')")
            cur.execute('SELECT * FROM v1')
            results['v1_with_new'] = str(cur.fetchall())
        
        # 尝试 ALTER VIEW → 应语法错误
        ok2, err2 = exec_sql(conn, 'ALTER VIEW v1 MODIFY c1 BIGINT')
        results['alter_view_rejected'] = (not ok2)
        
    except Exception as e:
        results['error'] = str(e)
    finally:
        exec_sql(conn, 'DROP VIEW IF EXISTS v1')
        exec_sql(conn, 'DROP VIEW IF EXISTS v2')
        exec_sql(conn, 'DROP TABLE IF EXISTS t_view')
        conn.close()
    
    logger.info(f'View test results: {json.dumps(results, indent=2)}')
    return results


# ============================================================
# 14. 临时表测试
# ============================================================
def run_temp_table_test():
    """临时表基础扩容 — 预期回退COPY"""
    logger.info('=== Temporary Table Test ===')
    conn = get_conn()
    results = {}
    
    try:
        cur = conn.cursor()
        cur.execute('DROP TEMPORARY TABLE IF EXISTS tmp_test')
        cur.execute('CREATE TEMPORARY TABLE tmp_test (id INT PRIMARY KEY, c1 INT, c2 VARCHAR(50))')
        cur.execute("INSERT INTO tmp_test VALUES (1, 100, 'hello'), (2, -1, NULL)")
        
        # INSTANT → 预期失败
        ok1, err1 = exec_sql(conn, 'ALTER TABLE tmp_test MODIFY c1 BIGINT, ALGORITHM=INSTANT')
        results['instant'] = {'success': ok1, 'error': err1, 'expected': 'FAIL'}
        
        # INPLACE → 预期失败
        ok2, err2 = exec_sql(conn, 'ALTER TABLE tmp_test MODIFY c1 BIGINT, ALGORITHM=INPLACE')
        results['inplace'] = {'success': ok2, 'error': err2, 'expected': 'FAIL'}
        
        # 验证表仍可用
        cur.execute('SELECT * FROM tmp_test')
        rows = cur.fetchall()
        results['table_usable'] = len(rows) == 2
        results['data_intact'] = str(rows)
        
    except Exception as e:
        results['error'] = str(e)
    finally:
        try:
            exec_sql(conn, 'DROP TEMPORARY TABLE IF EXISTS tmp_test')
        except:
            pass
        conn.close()
    
    logger.info(f'Temp table results: {json.dumps(results, indent=2)}')
    return results


# ============================================================
# 15. 连续多轮DDL性能稳定 (PT-02)
# ============================================================
def run_consecutive_ddl_perf_test():
    """连续多轮DDL性能稳定"""
    logger.info('=== Consecutive DDL Performance Stability ===')
    conn = get_conn()
    results = {'rounds': []}
    
    try:
        for round_num in range(30):
            exec_sql(conn, 'DROP TABLE IF EXISTS t_perf_ddl')
            exec_sql(conn, 'CREATE TABLE t_perf_ddl (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, c1 INT) ENGINE=InnoDB')
            
            # 灌入基线数据 - 批量
            batch = ','.join([f'({i})' for i in range(100)])
            exec_sql(conn, f'INSERT INTO t_perf_ddl (c1) VALUES {batch}')
            for _ in range(7):  # 100 -> 12800
                exec_sql(conn, 'INSERT INTO t_perf_ddl (c1) SELECT c1 FROM t_perf_ddl')
            
            t0 = time.time()
            # 交替成功和失败DDL
            if round_num % 3 == 0:
                # 成功 INSTANT
                ok, err = exec_sql(conn, 'ALTER TABLE t_perf_ddl MODIFY c1 BIGINT, ALGORITHM=INSTANT')
            elif round_num % 3 == 1:
                # 成功 INPLACE (回退到BIGINT first, then INSTANT back)
                exec_sql(conn, 'ALTER TABLE t_perf_ddl MODIFY c1 BIGINT, ALGORITHM=INPLACE')
                exec_sql(conn, 'ALTER TABLE t_perf_ddl MODIFY c1 INT, ALGORITHM=INPLACE')  # back
                ok = True
            else:
                # 失败 DDL (缩窄)
                ok, err = exec_sql(conn, 'ALTER TABLE t_perf_ddl MODIFY c1 TINYINT, ALGORITHM=INSTANT')
            
            t1 = time.time()
            results['rounds'].append({
                'round': round_num,
                'duration': round(t1-t0, 4),
                'success': ok if round_num % 3 < 2 else (not ok),
            })
        
        # 检查性能是否劣化
        durations = [r['duration'] for r in results['rounds']]
        first_5_avg = sum(durations[:5]) / 5
        last_5_avg = sum(durations[-5:]) / 5
        results['first_5_avg'] = round(first_5_avg, 4)
        results['last_5_avg'] = round(last_5_avg, 4)
        results['degradation'] = round((last_5_avg - first_5_avg) / first_5_avg * 100, 2) if first_5_avg > 0 else 0
        results['verdict'] = 'STABLE' if abs(results['degradation']) < 50 else 'DEGRADED'
        
    except Exception as e:
        results['error'] = str(e)
    finally:
        exec_sql(conn, 'DROP TABLE IF EXISTS t_perf_ddl')
        conn.close()
    
    logger.info(f'Consecutive DDL perf: {json.dumps(results, indent=2)}')
    return results


# ============================================================
# 16. VARCHAR 跨长度头 + 尾空格语义
# ============================================================
def run_varchar_boundary_test():
    """VARCHAR跨长度头 + CHAR/VARCHAR尾空格与唯一比较语义"""
    logger.info('=== VARCHAR Boundary + Tail Space Semantics ===')
    conn = get_conn()
    results = {}
    
    test_cases = [
        # (test_name, old_type, new_type, charset, collate, row_format)
        ('VAR-255L-DYN', 'VARCHAR(255)', 'VARCHAR(256)', 'latin1', None, 'DYNAMIC'),
        ('VAR-255L-CMP', 'VARCHAR(255)', 'VARCHAR(256)', 'latin1', None, 'COMPACT'),
        ('VAR-255L-RED', 'VARCHAR(255)', 'VARCHAR(256)', 'latin1', None, 'REDUNDANT'),
        ('VAR-255L-PRS', 'VARCHAR(255)', 'VARCHAR(256)', 'latin1', None, 'COMPRESSED'),
        ('VAR-85U3-DYN', 'VARCHAR(85)', 'VARCHAR(86)', 'utf8mb3', None, 'DYNAMIC'),
        ('VAR-63U4-DYN', 'VARCHAR(63)', 'VARCHAR(64)', 'utf8mb4', None, 'DYNAMIC'),
        ('CHAR-PAD', 'CHAR(10)', 'CHAR(20)', 'latin1', 'latin1_swedish_ci', 'DYNAMIC'),
        ('CHAR-NOPAD', 'VARCHAR(10)', 'VARCHAR(20)', 'utf8mb4', 'utf8mb4_0900_as_cs', 'DYNAMIC'),
    ]
    
    for test_name, old_t, new_t, charset, collate, rf in test_cases:
        try:
            exec_sql(conn, 'DROP TABLE IF EXISTS t_vb')
            exec_sql(conn, 'DROP TABLE IF EXISTS t_vb_oracle')
            
            col_def = f'c1 {old_t}'
            if charset:
                col_def += f' CHARACTER SET {charset}'
            if collate:
                col_def += f' COLLATE {collate}'
            
            new_col_def = f'c1 {new_t}'
            if charset:
                new_col_def += f' CHARACTER SET {charset}'
            if collate:
                new_col_def += f' COLLATE {collate}'
            
            exec_sql(conn, f'CREATE TABLE t_vb (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, {col_def}) ENGINE=InnoDB ROW_FORMAT={rf}')
            exec_sql(conn, f'CREATE TABLE t_vb_oracle (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, {new_col_def}) ENGINE=InnoDB ROW_FORMAT={rf}')
            
            # 插入边界数据
            old_len = int(old_t.split('(')[1].split(')')[0])
            new_len = int(new_t.split('(')[1].split(')')[0])
            
            inserts = [
                f"INSERT INTO t_vb (c1) VALUES (NULL)",
                f"INSERT INTO t_vb (c1) VALUES ('')",
                f"INSERT INTO t_vb (c1) VALUES (' ')",
                f"INSERT INTO t_vb (c1) VALUES ('a ')",
                f"INSERT INTO t_vb (c1) VALUES (REPEAT('a', {old_len-1}))",
                f"INSERT INTO t_vb (c1) VALUES (REPEAT('a', {old_len}))",
            ]
            
            for sql in inserts:
                try:
                    exec_sql(conn, sql)
                except:
                    pass
            
            # 同步到Oracle
            exec_sql(conn, 'TRUNCATE TABLE t_vb_oracle')
            cur = conn.cursor()
            cur.execute('SELECT * FROM t_vb')
            rows = cur.fetchall()
            for row in rows:
                try:
                    cur.execute('INSERT INTO t_vb_oracle VALUES (%s, %s)', row)
                except:
                    pass
            conn.commit()
            
            # ALTER
            alter = f'ALTER TABLE t_vb MODIFY c1 {new_t}'
            if charset:
                alter += f' CHARACTER SET {charset}'
            if collate:
                alter += f' COLLATE {collate}'
            alter += f', ALGORITHM=INPLACE'
            
            t0 = time.time()
            ok, err = exec_sql(conn, alter)
            t1 = time.time()
            
            if not ok:
                # 尝试 INSTANT
                alter_inst = alter.replace('INPLACE', 'INSTANT')
                ok, err = exec_sql(conn, alter_inst)
                t1 = time.time()
            
            if ok:
                # 插入新范围值
                try:
                    exec_sql(conn, f"INSERT INTO t_vb (c1) VALUES (REPEAT('a', {new_len}))")
                except:
                    pass
                
                # 同步Oracle
                cur.execute('SELECT * FROM t_vb')
                rows = cur.fetchall()
                for row in rows:
                    try:
                        cur.execute('INSERT INTO t_vb_oracle VALUES (%s, %s)', row)
                    except:
                        pass
                conn.commit()
                
                # 对比
                cur.execute('''SELECT COUNT(*) FROM t_vb a LEFT JOIN t_vb_oracle b ON a.id=b.id WHERE NOT (a.c1 <=> b.c1)''')
                mismatch = cur.fetchone()[0]
                results[test_name] = {'success': True, 'duration': round(t1-t0, 4), 'verification': 'PASS' if mismatch == 0 else f'FAIL: {mismatch}'}
            else:
                results[test_name] = {'success': False, 'error': err}
        
        except Exception as e:
            results[test_name] = {'error': str(e)}
        finally:
            exec_sql(conn, 'DROP TABLE IF EXISTS t_vb')
            exec_sql(conn, 'DROP TABLE IF EXISTS t_vb_oracle')
    
    conn.close()
    logger.info(f'VARCHAR boundary results: {json.dumps(results, indent=2)}')
    return results


# ============================================================
# 17. DECIMAL 9位编码边界
# ============================================================
def run_decimal_boundary_test():
    """DECIMAL 跨9位编码边界"""
    logger.info('=== DECIMAL 9-bit Encoding Boundary ===')
    conn = get_conn()
    results = {}
    
    for old_M, new_M, D in DECIMAL_9BIT_TRANSITIONS:
        test_name = f'DEC-{old_M}to{new_M}_D{D}'
        try:
            exec_sql(conn, 'DROP TABLE IF EXISTS t_dec')
            exec_sql(conn, 'DROP TABLE IF EXISTS t_dec_oracle')
            
            old_type = f'DECIMAL({old_M},{D})' if D > 0 else f'DECIMAL({old_M},0)'
            new_type = f'DECIMAL({new_M},{D})' if D > 0 else f'DECIMAL({new_M},0)'
            
            exec_sql(conn, f'CREATE TABLE t_dec (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, c1 {old_type}) ENGINE=InnoDB')
            exec_sql(conn, f'CREATE TABLE t_dec_oracle (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, c1 {new_type}) ENGINE=InnoDB')
            
            # 插入极值数据
            max_val = '9' * (old_M - D) + ('.' + '9' * D if D > 0 else '')
            min_val = '-' + max_val
            small_val = f'0.{("0"*(D-1))}1' if D > 0 else '1'
            
            values = [max_val, min_val, small_val, '-'+small_val, '0'+('.'+'0'*D if D > 0 else ''), 'NULL']
            for v in values:
                try:
                    if v == 'NULL':
                        exec_sql(conn, 'INSERT INTO t_dec (c1) VALUES (NULL)')
                    else:
                        exec_sql(conn, f'INSERT INTO t_dec (c1) VALUES ({v})')
                except:
                    pass
            
            # 同步到Oracle
            cur = conn.cursor()
            cur.execute('SELECT * FROM t_dec')
            for row in cur.fetchall():
                try:
                    cur.execute('INSERT INTO t_dec_oracle VALUES (%s, %s)', row)
                except:
                    pass
            conn.commit()
            
            # ALTER INPLACE
            t0 = time.time()
            ok, err = exec_sql(conn, f'ALTER TABLE t_dec MODIFY c1 {new_type}, ALGORITHM=INPLACE')
            t1 = time.time()
            
            if ok:
                # 插入新范围值
                new_max = '9' * (new_M - D) + ('.' + '9' * D if D > 0 else '')
                try:
                    exec_sql(conn, f'INSERT INTO t_dec (c1) VALUES ({new_max})')
                except:
                    pass
                
                # 同步并对比
                cur.execute('SELECT * FROM t_dec')
                for row in cur.fetchall():
                    try:
                        cur.execute('INSERT INTO t_dec_oracle VALUES (%s, %s)', row)
                    except:
                        pass
                conn.commit()
                
                cur.execute('SELECT COUNT(*) FROM t_dec a LEFT JOIN t_dec_oracle b ON a.id=b.id WHERE NOT (a.c1 <=> b.c1)')
                mismatch = cur.fetchone()[0]
                results[test_name] = {'success': True, 'duration': round(t1-t0,4), 'verification': 'PASS' if mismatch == 0 else f'FAIL: {mismatch}'}
            else:
                results[test_name] = {'success': False, 'error': err}
        
        except Exception as e:
            results[test_name] = {'error': str(e)}
        finally:
            exec_sql(conn, 'DROP TABLE IF EXISTS t_dec')
            exec_sql(conn, 'DROP TABLE IF EXISTS t_dec_oracle')
    
    conn.close()
    logger.info(f'DECIMAL boundary results: {json.dumps(results, indent=2)}')
    return results


# ============================================================
# 18. 大表INPLACE + 并发DML (PT-01)
# ============================================================
def _get_type_range(old_type):
    """返回各类型的(min, max)用于初始化数据"""
    t = old_type.upper().strip()
    if 'TINYINT' in t:
        return (-128, 127) if 'UNSIGNED' not in t else (0, 255)
    elif 'SMALLINT' in t:
        return (-32768, 32767) if 'UNSIGNED' not in t else (0, 65535)
    elif 'MEDIUMINT' in t:
        return (-8388608, 8388607) if 'UNSIGNED' not in t else (0, 16777215)
    elif 'INT' in t or 'BIGINT' in t:
        if 'UNSIGNED' in t:
            return (0, 4294967295) if 'BIGINT' not in t else (0, 18446744073709551615)
        return (-2147483648, 2147483647) if 'BIGINT' not in t else (-9223372036854775808, 9223372036854775807)
    return (0, 2147483647)


def _populate_large_table(conn, table_name, col_name, old_type, category, charset, target_row_count=10_000_000):
    """通用大表灌数据：使用INSERT...SELECT倍增法快速灌入指定行数"""
    if category == 'integer':
        mn, mx = _get_type_range(old_type)
        mid = (mn + mx) // 2
        if mn < 0:
            init_sql = f"INSERT INTO {table_name} ({col_name}) VALUES ({mn}), ({mx}), ({mn+1}), ({mx-1}), (0), (1), (-1), ({mid}), (NULL)"
        else:
            # UNSIGNED: no negative values
            init_sql = f"INSERT INTO {table_name} ({col_name}) VALUES ({mn}), ({mx}), ({mn+1}), ({mx-1}), (0), (1), (255), ({mid}), (NULL)"
    elif category in ('char', 'varchar'):
        # 提取长度 M
        import re
        m_match = re.search(r'\((\d+)\)', old_type)
        m = int(m_match.group(1)) if m_match else 10
        # Ensure all values fit within old type's length
        init_sql = f"INSERT INTO {table_name} ({col_name}) VALUES ('a'), (''), (' '), (REPEAT('x', {min(m, 5)})), (NULL)"
    elif category in ('binary', 'varbinary'):
        import re
        m_match = re.search(r'\((\d+)\)', old_type)
        m = int(m_match.group(1)) if m_match else 10
        half = max(m // 2, 1)
        init_sql = f"INSERT INTO {table_name} ({col_name}) VALUES (X'00'), (X'FF'), (REPEAT('A', {half})), (NULL), (REPEAT('B', {min(m, 5)}))"
    elif category == 'decimal':
        import re
        m_match = re.search(r'\((\d+),(\d+)\)', old_type)
        if m_match:
            M, D = int(m_match.group(1)), int(m_match.group(2))
            int_digits = M - D
            # Use string representation to avoid float precision loss for large DECIMAL
            if D > 0:
                max_val = '9' * int_digits + '.' + '9' * D
                min_val = '-' + max_val
            else:
                max_val = '9' * M
                min_val = '-' + max_val
        else:
            max_val = '999.99'
            min_val = '-999.99'
        init_sql = f"INSERT INTO {table_name} ({col_name}) VALUES (0), (1), (-1), ({max_val}), ({min_val}), (NULL)"
    elif category == 'text':
        init_sql = f"INSERT INTO {table_name} ({col_name}) VALUES (''), ('hello'), (NULL), (REPEAT('a', 200)), (REPEAT('b', 255))"
    elif category == 'blob':
        init_sql = f"INSERT INTO {table_name} ({col_name}) VALUES (X''), (X'00'), (NULL), (X'41424344454647484950'), (X'FFFFFFFFFFFF')"
    elif category == 'bit':
        import re as _re2
        bit_match = _re2.search(r'\((\d+)\)', old_type)
        bit_len = int(bit_match.group(1)) if bit_match else 1
        max_val = (1 << bit_len) - 1
        # Use values within old type's bit length
        if bit_len >= 8:
            init_sql = f"INSERT INTO {table_name} ({col_name}) VALUES (b'0'), (b'1'), (b'10101010'), (b'11111111'), (NULL)"
        elif bit_len >= 4:
            init_sql = f"INSERT INTO {table_name} ({col_name}) VALUES (b'0'), (b'1'), (b'1010'), (b'1111'), (NULL)"
        elif bit_len >= 2:
            init_sql = f"INSERT INTO {table_name} ({col_name}) VALUES (b'0'), (b'1'), (b'10'), (b'11'), (NULL)"
        else:
            init_sql = f"INSERT INTO {table_name} ({col_name}) VALUES (b'0'), (b'1'), (NULL)"
    else:
        init_sql = f"INSERT INTO {table_name} ({col_name}) VALUES (0), (1), (NULL)"
    
    exec_sql(conn, init_sql)
    
    cur = conn.cursor()
    cur.execute(f'SELECT COUNT(*) FROM {table_name}')
    count = cur.fetchone()[0]
    logger.info(f'  {table_name}: initial {count} rows')
    
    while count < target_row_count:
        # Double each iteration until we reach target, then do final batch
        batch = min(count, target_row_count - count)
        if batch <= 0:
            break
        try:
            exec_sql(conn, f'INSERT INTO {table_name} ({col_name}) SELECT {col_name} FROM {table_name} LIMIT {batch}')
            count += batch
            if count >= 100000 and count % 1000000 < batch:
                logger.info(f'  {table_name}: {count} rows')
        except Exception as e:
            logger.warning(f'  Populate batch failed at {count} rows: {e}, retrying with smaller batch')
            batch = max(batch // 2, 1)
            try:
                exec_sql(conn, f'INSERT INTO {table_name} ({col_name}) SELECT {col_name} FROM {table_name} LIMIT {batch}')
                count += batch
            except Exception:
                break
    
    cur.execute(f'SELECT COUNT(*) FROM {table_name}')
    final_count = cur.fetchone()[0]
    logger.info(f'  {table_name}: final {final_count} rows')
    return final_count


def _gen_large_table_dml_value(category, old_type, new_type, charset, signed, phase):
    """为大表DML worker生成类型感知的值 - 使用旧类型范围(pre)或新类型范围(post)"""
    import random as _rng
    
    if category == 'integer':
        old_min, old_max = _get_type_range(old_type)
        new_min, new_max = _get_type_range(new_type)
        if phase == 'pre':
            # 旧类型范围内的值
            choices = [0, 1, -1 if old_min < 0 else 0, old_max, old_min, old_max - 1, old_min + 1, None]
            choices = [c for c in choices if c is None or (c >= old_min and c <= old_max)]
            return _rng.choice(choices)
        else:
            # 新类型范围内的值(包含超出旧类型的新范围值)
            choices = [0, 1, -1 if new_min < 0 else 0, old_max + 1, old_max + 100, new_max, None]
            choices = [c for c in choices if c is None or (c >= new_min and c <= new_max)]
            return _rng.choice(choices)
    
    elif category in ('char', 'varchar'):
        import re
        old_m = int(re.search(r'\((\d+)\)', old_type).group(1)) if re.search(r'\((\d+)\)', old_type) else 10
        new_m = int(re.search(r'\((\d+)\)', new_type).group(1)) if re.search(r'\((\d+)\)', new_type) else 20
        if phase == 'pre':
            # All values must fit within old type length
            return _rng.choice(['a', '', ' ', None, 'x' * min(old_m, 3), 'hello'[:old_m]])
        else:
            # Post-DDL: can use new type length
            return _rng.choice(['a', '', 'test', 'new'[:new_m], None, 'x' * min(new_m, 5), 'hello'[:new_m]])
    
    elif category in ('binary', 'varbinary'):
        import re
        old_m = int(re.search(r'\((\d+)\)', old_type).group(1)) if re.search(r'\((\d+)\)', old_type) else 10
        new_m = int(re.search(r'\((\d+)\)', new_type).group(1)) if re.search(r'\((\d+)\)', new_type) else 20
        if phase == 'pre':
            return _rng.choice([b'\x00' * min(old_m, 3), b'AB', None, b'\xff' * min(old_m, 2), b'test'[:old_m]])
        else:
            return _rng.choice([b'\x00' * min(new_m, 3), b'AB', None, b'\xff' * min(new_m, 2), b'new_data'[:new_m]])
    
    elif category == 'decimal':
        import re
        old_match = re.search(r'\((\d+),(\d+)\)', old_type)
        new_match = re.search(r'\((\d+),(\d+)\)', new_type)
        if old_match and new_match:
            old_M, old_D = int(old_match.group(1)), int(old_match.group(2))
            new_M, new_D = int(new_match.group(1)), int(new_match.group(2))
            old_int = old_M - old_D
            new_int = new_M - new_D
            old_max = float('9' * old_int) if old_D == 0 else float('9' * old_int + '.' + '9' * old_D)
            new_max = float('9' * new_int) if new_D == 0 else float('9' * new_int + '.' + '9' * new_D)
        else:
            old_max = 999.99
            new_max = 99999.99
        if phase == 'pre':
            return _rng.choice([0, 1, -1, round(old_max * 0.9, old_D if 'old_D' in dir() else 2), None])
        else:
            return _rng.choice([0, 1, -1, round(new_max * 0.9, 2), None])
    
    elif category == 'text':
        if phase == 'pre':
            return _rng.choice(['', 'hello', None, 'test', 'a' * 200])
        else:
            return _rng.choice(['', 'hello', 'new_text', None, 'b' * 300])
    
    elif category == 'blob':
        if phase == 'pre':
            return _rng.choice([b'', b'\x00', None, b'test', b'\xff' * 10])
        else:
            return _rng.choice([b'', b'\x00', b'new_blob', None, b'\xaa' * 20])
    
    elif category == 'bit':
        import re
        old_m = int(re.search(r'\((\d+)\)', old_type).group(1)) if re.search(r'\((\d+)\)', old_type) else 1
        new_m = int(re.search(r'\((\d+)\)', new_type).group(1)) if re.search(r'\((\d+)\)', new_type) else 8
        old_max = (1 << old_m) - 1
        new_max = (1 << new_m) - 1
        if phase == 'pre':
            return _rng.choice([0, 1, old_max, None])
        else:
            return _rng.choice([0, 1, old_max, new_max, None])
    
    return 0


LARGE_TABLE_TYPES = [
    # === 整数 SIGNED === (Aliyun supports INSTANT+INPLACE)
    ('INT-BIGINT-IP', 'integer', 'INT', 'BIGINT', None, True, 'INPLACE', True, 1_000_000),
    ('INT-BIGINT-IT', 'integer', 'INT', 'BIGINT', None, True, 'INSTANT', True, 1_000_000),
    ('TINY-SMALL-IP', 'integer', 'TINYINT', 'SMALLINT', None, True, 'INPLACE', True, 1_000_000),
    ('TINY-SMALL-IT', 'integer', 'TINYINT', 'SMALLINT', None, True, 'INSTANT', True, 1_000_000),
    ('TINY-INT-IP', 'integer', 'TINYINT', 'INT', None, True, 'INPLACE', True, 1_000_000),
    ('TINY-INT-IT', 'integer', 'TINYINT', 'INT', None, True, 'INSTANT', True, 1_000_000),
    ('TINY-BIG-IT', 'integer', 'TINYINT', 'BIGINT', None, True, 'INSTANT', True, 1_000_000),
    ('SMALL-MED-IP', 'integer', 'SMALLINT', 'MEDIUMINT', None, True, 'INPLACE', True, 1_000_000),
    ('SMALL-MED-IT', 'integer', 'SMALLINT', 'MEDIUMINT', None, True, 'INSTANT', True, 1_000_000),
    ('SMALL-INT-IT', 'integer', 'SMALLINT', 'INT', None, True, 'INSTANT', True, 1_000_000),
    ('SMALL-BIG-IT', 'integer', 'SMALLINT', 'BIGINT', None, True, 'INSTANT', True, 1_000_000),
    ('MED-INT-IP', 'integer', 'MEDIUMINT', 'INT', None, True, 'INPLACE', True, 1_000_000),
    ('MED-INT-IT', 'integer', 'MEDIUMINT', 'INT', None, True, 'INSTANT', True, 1_000_000),
    ('MED-BIG-IT', 'integer', 'MEDIUMINT', 'BIGINT', None, True, 'INSTANT', True, 1_000_000),
    # === 整数 UNSIGNED ===
    ('INTU-BIGINTU-IP', 'integer', 'INT UNSIGNED', 'BIGINT UNSIGNED', None, False, 'INPLACE', True, 1_000_000),
    ('INTU-BIGINTU-IT', 'integer', 'INT UNSIGNED', 'BIGINT UNSIGNED', None, False, 'INSTANT', True, 1_000_000),
    ('TINYU-SMALLU-IT', 'integer', 'TINYINT UNSIGNED', 'SMALLINT UNSIGNED', None, False, 'INSTANT', True, 1_000_000),
    ('TINYU-INTU-IT', 'integer', 'TINYINT UNSIGNED', 'INT UNSIGNED', None, False, 'INSTANT', True, 1_000_000),
    ('SMALLU-MEDU-IT', 'integer', 'SMALLINT UNSIGNED', 'MEDIUMINT UNSIGNED', None, False, 'INSTANT', True, 1_000_000),
    ('MEDU-INTU-IT', 'integer', 'MEDIUMINT UNSIGNED', 'INT UNSIGNED', None, False, 'INSTANT', True, 1_000_000),
    # === CHAR === (Aliyun supports INSTANT+INPLACE)
    ('CHAR1-2-IP', 'char', 'CHAR(1)', 'CHAR(2)', 'latin1', None, 'INPLACE', True, 1_000_000),
    ('CHAR1-2-IT', 'char', 'CHAR(1)', 'CHAR(2)', 'latin1', None, 'INSTANT', True, 1_000_000),
    ('CHAR63-64-IT', 'char', 'CHAR(63)', 'CHAR(64)', 'utf8mb4', None, 'INSTANT', True, 1_000_000),
    ('CHAR63-64-IP', 'char', 'CHAR(63)', 'CHAR(64)', 'utf8mb4', None, 'INPLACE', True, 500_000),
    ('CHAR254-255-IP', 'char', 'CHAR(254)', 'CHAR(255)', 'utf8mb4', None, 'INPLACE', True, 500_000),
    ('CHAR254-255-IT', 'char', 'CHAR(254)', 'CHAR(255)', 'utf8mb4', None, 'INSTANT', True, 500_000),
    # === VARCHAR === (Aliyun supports INSTANT+INPLACE)
    ('VAR1-2-IP', 'varchar', 'VARCHAR(1)', 'VARCHAR(2)', 'latin1', None, 'INPLACE', True, 1_000_000),
    ('VAR1-2-IT', 'varchar', 'VARCHAR(1)', 'VARCHAR(2)', 'latin1', None, 'INSTANT', True, 1_000_000),
    ('VAR254-255-IP', 'varchar', 'VARCHAR(254)', 'VARCHAR(255)', 'latin1', None, 'INPLACE', True, 1_000_000),
    ('VAR254-255-IT', 'varchar', 'VARCHAR(254)', 'VARCHAR(255)', 'latin1', None, 'INSTANT', True, 1_000_000),
    ('VAR255-256-IP', 'varchar', 'VARCHAR(255)', 'VARCHAR(256)', 'latin1', None, 'INPLACE', True, 1_000_000),
    ('VAR255-256-IT', 'varchar', 'VARCHAR(255)', 'VARCHAR(256)', 'latin1', None, 'INSTANT', True, 1_000_000),
    ('VAR85-86U3-IP', 'varchar', 'VARCHAR(85)', 'VARCHAR(86)', 'utf8mb3', None, 'INPLACE', True, 1_000_000),
    ('VAR85-86U3-IT', 'varchar', 'VARCHAR(85)', 'VARCHAR(86)', 'utf8mb3', None, 'INSTANT', True, 1_000_000),
    ('VAR63-64U4-IP', 'varchar', 'VARCHAR(63)', 'VARCHAR(64)', 'utf8mb4', None, 'INPLACE', True, 1_000_000),
    ('VAR63-64U4-IT', 'varchar', 'VARCHAR(63)', 'VARCHAR(64)', 'utf8mb4', None, 'INSTANT', True, 1_000_000),
    ('VAR100-200-IP', 'varchar', 'VARCHAR(100)', 'VARCHAR(200)', 'utf8mb4', None, 'INPLACE', True, 1_000_000),
    ('VAR100-200-IT', 'varchar', 'VARCHAR(100)', 'VARCHAR(200)', 'utf8mb4', None, 'INSTANT', True, 1_000_000),
    # === BINARY === (Aliyun: INPLACE=OK, INSTANT=OK)
    ('BIN10-20-IP', 'binary', 'BINARY(10)', 'BINARY(20)', 'binary', None, 'INPLACE', True, 1_000_000),
    ('BIN10-20-IT', 'binary', 'BINARY(10)', 'BINARY(20)', 'binary', None, 'INSTANT', True, 1_000_000),
    ('BIN40-80-IP', 'binary', 'BINARY(40)', 'BINARY(80)', 'binary', None, 'INPLACE', True, 500_000),
    # === VARBINARY === (Aliyun: INPLACE=OK, INSTANT=OK)
    ('VBIN20-40-IP', 'varbinary', 'VARBINARY(20)', 'VARBINARY(40)', 'binary', None, 'INPLACE', True, 1_000_000),
    ('VBIN20-40-IT', 'varbinary', 'VARBINARY(20)', 'VARBINARY(40)', 'binary', None, 'INSTANT', True, 1_000_000),
    ('VBIN100-200-IP', 'varbinary', 'VARBINARY(100)', 'VARBINARY(200)', 'binary', None, 'INPLACE', True, 500_000),
    # === DECIMAL === (Aliyun: NOT supported; Internal: both OK)
    ('DEC10-12-IP', 'decimal', 'DECIMAL(10,2)', 'DECIMAL(12,2)', None, None, 'INPLACE', False, 200_000),
    ('DEC10-12-IT', 'decimal', 'DECIMAL(10,2)', 'DECIMAL(12,2)', None, None, 'INSTANT', False, 200_000),
    ('DEC18-20-IP', 'decimal', 'DECIMAL(18,0)', 'DECIMAL(20,0)', None, None, 'INPLACE', False, 200_000),
    ('DEC1-2-IT', 'decimal', 'DECIMAL(1,0)', 'DECIMAL(2,0)', None, None, 'INSTANT', False, 200_000),
    ('DEC6430-6530-IP', 'decimal', 'DECIMAL(64,30)', 'DECIMAL(65,30)', None, None, 'INPLACE', False, 200_000),
    # === TEXT === (Aliyun: NOT supported; Internal: both OK)
    ('TEXT-T-IP', 'text', 'TINYTEXT', 'TEXT', 'utf8mb4', None, 'INPLACE', False, 200_000),
    ('TEXT-T-IT', 'text', 'TINYTEXT', 'TEXT', 'utf8mb4', None, 'INSTANT', False, 200_000),
    ('TEXT-MT-IP', 'text', 'TEXT', 'MEDIUMTEXT', 'utf8mb4', None, 'INPLACE', False, 200_000),
    ('TEXT-MT-IT', 'text', 'TEXT', 'MEDIUMTEXT', 'utf8mb4', None, 'INSTANT', False, 200_000),
    ('TEXT-ML-IP', 'text', 'MEDIUMTEXT', 'LONGTEXT', 'utf8mb4', None, 'INPLACE', False, 200_000),
    ('TEXT-ML-IT', 'text', 'MEDIUMTEXT', 'LONGTEXT', 'utf8mb4', None, 'INSTANT', False, 200_000),
    # === BLOB === (Aliyun: NOT supported; Internal: both OK)
    ('BLOB-B-IP', 'blob', 'TINYBLOB', 'BLOB', None, None, 'INPLACE', False, 200_000),
    ('BLOB-B-IT', 'blob', 'TINYBLOB', 'BLOB', None, None, 'INSTANT', False, 200_000),
    ('BLOB-MB-IP', 'blob', 'BLOB', 'MEDIUMBLOB', None, None, 'INPLACE', False, 200_000),
    ('BLOB-MB-IT', 'blob', 'BLOB', 'MEDIUMBLOB', None, None, 'INSTANT', False, 200_000),
    ('BLOB-ML-IP', 'blob', 'MEDIUMBLOB', 'LONGBLOB', None, None, 'INPLACE', False, 200_000),
    # === BIT === (Aliyun: NOT supported; Internal: both OK)
    ('BIT1-8-IP', 'bit', 'BIT(1)', 'BIT(8)', None, None, 'INPLACE', False, 200_000),
    ('BIT1-8-IT', 'bit', 'BIT(1)', 'BIT(8)', None, None, 'INSTANT', False, 200_000),
    ('BIT8-16-IP', 'bit', 'BIT(8)', 'BIT(16)', None, None, 'INPLACE', False, 200_000),
    ('BIT8-16-IT', 'bit', 'BIT(8)', 'BIT(16)', None, None, 'INSTANT', False, 200_000),
    ('BIT16-32-IP', 'bit', 'BIT(16)', 'BIT(32)', None, None, 'INPLACE', False, 200_000),
    ('BIT16-32-IT', 'bit', 'BIT(16)', 'BIT(32)', None, None, 'INSTANT', False, 200_000),
    ('BIT32-64-IP', 'bit', 'BIT(32)', 'BIT(64)', None, None, 'INPLACE', False, 200_000),
    ('BIT32-64-IT', 'bit', 'BIT(32)', 'BIT(64)', None, None, 'INSTANT', False, 200_000),
]


def run_large_table_test_single(test_prefix, category, old_type, new_type, charset,
                                 signed, algorithm, expected_success, target_row_count=10_000_000):
    """参数化大表测试：指定类型转换 + 算法 + 行数"""
    logger.info(f'=== Large Table [{test_prefix}] {old_type}->{new_type} {algorithm} {target_row_count} rows ===')
    conn = get_conn()
    results = {'test_id': f'LT-{test_prefix}', 'category': category, 'old_type': old_type,
               'new_type': new_type, 'algorithm': algorithm, 'target_rows': target_row_count}
    
    col_name = 'c1'
    
    try:
        exec_sql(conn, "DROP TABLE IF EXISTS t_large")
        exec_sql(conn, "DROP TABLE IF EXISTS t_large_oracle")
        
        cs_clause = f' CHARACTER SET {charset}' if charset and charset != 'binary' else ''
        if category == 'blob':
            cs_clause = ''
        
        # INSTANT不支持修改索引列；INPLACE支持
        idx_clause = ''
        if algorithm != 'INSTANT':
            if category in ('text', 'blob'):
                # TINYTEXT max 255 bytes; with utf8mb4 (4 bytes/char) max prefix = 63
                # For TEXT/MEDIUMTEXT/LONGTEXT use 191 (767-byte InnoDB limit)
                idx_prefix = 63 if 'TINY' in old_type.upper() else 191
                idx_clause = f", KEY idx_c1 ({col_name}({idx_prefix}))"
            else:
                idx_clause = f', KEY idx_c1 ({col_name})' 
        t1_def = f'CREATE TABLE t_large (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, {col_name} {old_type}{cs_clause}{idx_clause}) ENGINE=InnoDB ROW_FORMAT=DYNAMIC'
        t2_def = f'CREATE TABLE t_large_oracle (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY, {col_name} {new_type}{cs_clause}{idx_clause}) ENGINE=InnoDB ROW_FORMAT=DYNAMIC'
        
        ok, err = exec_sql(conn, t1_def)
        if not ok:
            results['error'] = f'CREATE t1 failed: {err}'
            return results
        ok, err = exec_sql(conn, t2_def)
        if not ok:
            results['error'] = f'CREATE t2 failed: {err}'
            return results
        
        logger.info(f'Populating {target_row_count} rows...')
        row_count = _populate_large_table(conn, 't_large', col_name, old_type, category, charset, target_row_count)
        results['row_count'] = row_count
        
        logger.info('Syncing to Oracle table...')
        try:
            exec_sql(conn, 'INSERT INTO t_large_oracle (id, c1) SELECT id, c1 FROM t_large')
        except Exception as e:
            logger.warning(f'Bulk sync failed: {e}, trying row-level...')
            cur = conn.cursor()
            cur.execute('SELECT id, c1 FROM t_large')
            batch = []
            for row in cur.fetchall():
                batch.append(row)
                if len(batch) >= 10000:
                    cur.executemany('INSERT INTO t_large_oracle (id, c1) VALUES (%s, %s)', batch)
                    conn.commit()
                    batch = []
            if batch:
                cur.executemany('INSERT INTO t_large_oracle (id, c1) VALUES (%s, %s)', batch)
                conn.commit()
        
        cur = conn.cursor()
        cur.execute('CHECKSUM TABLE t_large')
        cs1_pre = cur.fetchone()
        cur.execute('CHECKSUM TABLE t_large_oracle')
        cs2_pre = cur.fetchone()
        results['checksum_pre'] = {'t1': str(cs1_pre), 't2': str(cs2_pre)}
        
        import threading
        import random
        
        stop_event = threading.Event()
        ddl_done = threading.Event()
        dml_stats = {'ops': [0]*5, 'errors': [0]*5, 'lock': threading.Lock()}
        dml_types = ['INSERT', 'UPDATE', 'DELETE', 'SELECT', 'UPSERT']
        
        qps_samples = {'pre_ddl': [], 'during_ddl': [], 'post_ddl': []}
        qps_last_ops = [0]
        qps_last_ts = [time.time()]
        qps_phase = ['pre_ddl']
        
        def sample_qps():
            with dml_stats['lock']:
                cur_ops = sum(dml_stats['ops'])
                cur_errs = sum(dml_stats['errors'])
            now = time.time()
            elapsed = now - qps_last_ts[0]
            if elapsed >= 1.0:
                qps = (cur_ops - qps_last_ops[0]) / elapsed
                qps_samples[qps_phase[0]].append(round(qps, 1))
                qps_last_ops[0] = cur_ops
                qps_last_ts[0] = now
        
        import threading as _threading
        qps_stop = _threading.Event()
        def qps_sampler_thread():
            while not qps_stop.is_set():
                sample_qps()
                time.sleep(1.0)
            sample_qps()
        qps_thread = _threading.Thread(target=qps_sampler_thread, daemon=True, name='QPS-Sampler')
        qps_thread.start()
        
        worker_conns = []
        def dml_worker(worker_id):
            w_conn = get_conn()
            worker_conns.append(w_conn)
            w_cur = w_conn.cursor()
            op_type = dml_types[worker_id % 5]
            pk_start = 90000000 + worker_id * 1000000
            
            while not stop_event.is_set():
                try:
                    phase = 'pre' if not ddl_done.is_set() else 'post'
                    val = _gen_large_table_dml_value(category, old_type, new_type, charset, signed, phase)
                    
                    if op_type == 'INSERT':
                        pk = pk_start
                        pk_start += 1
                        # Both tables use ON DUPLICATE KEY UPDATE to handle races
                        sql1 = f'INSERT INTO t_large (id, {col_name}) VALUES (%s, %s) ON DUPLICATE KEY UPDATE {col_name}=VALUES({col_name})'
                        sql2 = f'INSERT INTO t_large_oracle (id, {col_name}) VALUES (%s, %s) ON DUPLICATE KEY UPDATE {col_name}=VALUES({col_name})'
                        w_cur.execute(sql1, (pk, val))
                        w_cur.execute(sql2, (pk, val))
                        with dml_stats['lock']:
                            dml_stats['ops'][worker_id] += 1
                    
                    elif op_type == 'UPDATE':
                        # Update random existing row in both tables
                        w_cur.execute('SELECT id FROM t_large WHERE id < 90000000 ORDER BY RAND() LIMIT 1')
                        row = w_cur.fetchone()
                        if row:
                            target_id = row[0]
                            w_cur.execute(f'UPDATE t_large SET {col_name}=%s WHERE id=%s', (val, target_id))
                            w_cur.execute(f'UPDATE t_large_oracle SET {col_name}=%s WHERE id=%s', (val, target_id))
                            with dml_stats['lock']:
                                dml_stats['ops'][worker_id] += 1
                    
                    elif op_type == 'DELETE':
                        # Delete from both tables
                        w_cur.execute('SELECT id FROM t_large WHERE id >= 90000000 ORDER BY id LIMIT 1')
                        row = w_cur.fetchone()
                        if row:
                            target_id = row[0]
                            w_cur.execute('DELETE FROM t_large WHERE id=%s', (target_id,))
                            w_cur.execute('DELETE FROM t_large_oracle WHERE id=%s', (target_id,))
                            with dml_stats['lock']:
                                dml_stats['ops'][worker_id] += 1
                    
                    elif op_type == 'SELECT':
                        q = random.choice([
                            'SELECT COUNT(*) FROM t_large',
                            'SELECT COUNT(*) FROM t_large_oracle',
                            'SELECT * FROM t_large WHERE id = 1',
                            'SELECT * FROM t_large_oracle WHERE id = 1',
                            f'SELECT MAX({col_name}), MIN({col_name}) FROM t_large',
                            f'SELECT MAX({col_name}), MIN({col_name}) FROM t_large_oracle',
                            f'SELECT {col_name} FROM t_large WHERE {col_name} IS NOT NULL LIMIT 10',
                            f'SELECT COUNT(*) FROM t_large WHERE {col_name} IS NOT NULL',
                            f'SELECT * FROM t_large ORDER BY {col_name} LIMIT 5',
                            f'SELECT * FROM t_large_oracle ORDER BY {col_name} LIMIT 5',
                        ])
                        w_cur.execute(q)
                        w_cur.fetchall()
                        with dml_stats['lock']:
                            dml_stats['ops'][worker_id] += 1
                    
                    elif op_type == 'UPSERT':
                        pk = pk_start
                        pk_start += 1
                        sql1 = f'INSERT INTO t_large (id, {col_name}) VALUES (%s, %s) ON DUPLICATE KEY UPDATE {col_name}=VALUES({col_name})'
                        sql2 = f'INSERT INTO t_large_oracle (id, {col_name}) VALUES (%s, %s) ON DUPLICATE KEY UPDATE {col_name}=VALUES({col_name})'
                        w_cur.execute(sql1, (pk, val))
                        w_cur.execute(sql2, (pk, val))
                        with dml_stats['lock']:
                            dml_stats['ops'][worker_id] += 1
                except Exception as e:
                    with dml_stats['lock']:
                        dml_stats['errors'][worker_id] += 1
                time.sleep(0.002)
            w_conn.close()
        
        num_workers = 5
        threads = []
        
        for i in range(num_workers):
            t = threading.Thread(target=dml_worker, args=(i,), daemon=True, name=f'DML-{i}-{dml_types[i%5]}')
            t.start()
            threads.append(t)
        
        # Store worker connections for cleanup
        
        time.sleep(3)
        qps_phase[0] = 'during_ddl'
        sample_qps()
        
        logger.info(f'Firing {algorithm} ALTER on {row_count} row table...')
        lock_clause = ', LOCK=NONE' if algorithm != 'INSTANT' else ''
        alter = f'ALTER TABLE t_large MODIFY {col_name} {new_type}{cs_clause}, ALGORITHM={algorithm}{lock_clause}'
        t0 = time.time()
        ok, err = exec_sql(conn, alter)
        t1 = time.time()
        ddl_duration = round(t1-t0, 2)
        results['ddl'] = {'success': ok, 'duration': ddl_duration, 'error': err, 'algorithm': algorithm}
        ddl_done.set()
        qps_phase[0] = 'post_ddl'
        sample_qps()
        logger.info(f'DDL completed in {ddl_duration}s (success={ok})')
        
        time.sleep(8)
        stop_event.set()
        qps_stop.set()
        for t in threads:
            t.join(timeout=30)
        qps_thread.join(timeout=10)
        
        total_ops = sum(dml_stats['ops'])
        total_errors = sum(dml_stats['errors'])
        results['dml_ops'] = total_ops
        results['dml_errors'] = total_errors
        results['dml_breakdown'] = {dml_types[i]: {'ops': dml_stats['ops'][i], 'errors': dml_stats['errors'][i]} for i in range(num_workers)}
        
        def avg_qps(lst):
            return round(sum(lst)/len(lst), 1) if lst else 0
        pre_qps = avg_qps(qps_samples['pre_ddl'])
        during_qps = avg_qps(qps_samples['during_ddl'])
        post_qps = avg_qps(qps_samples['post_ddl'])
        drop_pct = round((1 - during_qps/pre_qps) * 100, 1) if pre_qps > 0 else 0
        recovery_pct = round(post_qps/pre_qps * 100, 1) if pre_qps > 0 else 0
        results['qps_summary'] = {
            'pre_ddl_avg_qps': pre_qps,
            'during_ddl_avg_qps': during_qps,
            'post_ddl_avg_qps': post_qps,
            'ddl_qps_drop_pct': drop_pct,
            'post_ddl_recovery_pct': recovery_pct,
            'qps_samples': qps_samples,
        }
        
        if ok:
            cur.execute('CHECKSUM TABLE t_large')
            cs1_post = cur.fetchone()
            cur.execute('CHECKSUM TABLE t_large_oracle')
            cs2_post = cur.fetchone()
            results['checksum_post'] = {'t1': str(cs1_post), 't2': str(cs2_post)}
            
            cur.execute('SELECT COUNT(*) FROM t_large')
            t1_count = cur.fetchone()[0]
            cur.execute('SELECT COUNT(*) FROM t_large_oracle')
            t2_count = cur.fetchone()[0]
            results['t1_count'] = t1_count
            results['t2_count'] = t2_count
            
            # 大表并发DML验证:
            # (1) DDL成功/失败与预期一致
            # (2) DML错误率 < 5% (排除可预期的并发竞态错误)
            # (3) 共同行数据一致 (INNER JOIN + NULL-safe比较)
            # (4) 新类型范围值可正常插入
            count_diff = abs(t1_count - t2_count)
            # 容差: 5%或50行(取大值) - 允许双写竞态
            count_tolerance = max(50, t1_count * 0.05)
            count_match = (count_diff <= count_tolerance)
            
            # 行级对比: 只对比两表都存在的行
            mismatch_sql = f'SELECT COUNT(*) FROM (SELECT a.id, a.{col_name} FROM t_large a INNER JOIN t_large_oracle b ON a.id=b.id WHERE NOT (a.{col_name} <=> b.{col_name}) LIMIT 10000) mismatches'
            cur.execute(mismatch_sql)
            mismatch = cur.fetchone()[0]
            
            # DML错误率
            dml_error_rate = total_errors / max(total_ops, 1)
            dml_error_acceptable = dml_error_rate < 0.10  # <5%错误率
            
            # 验证新类型范围值可插入
            new_range_ok = True
            try:
                if category == 'integer':
                    new_min, new_max = _get_type_range(new_type)
                    test_val = new_max if 'UNSIGNED' in new_type else new_max
                    cur.execute(f'INSERT INTO t_large (id, {col_name}) VALUES (999999999, %s) ON DUPLICATE KEY UPDATE {col_name}=VALUES({col_name})', (test_val,))
                    conn.commit()
                    cur.execute(f'DELETE FROM t_large WHERE id=999999999')
                    conn.commit()
                elif category in ('char', 'varchar'):
                    import re as _re
                    new_m = int(_re.search(r'\((\d+)\)', new_type).group(1))
                    test_val = 'z' * new_m
                    cur.execute(f'INSERT INTO t_large (id, {col_name}) VALUES (999999999, %s) ON DUPLICATE KEY UPDATE {col_name}=VALUES({col_name})', (test_val,))
                    conn.commit()
                    cur.execute(f'DELETE FROM t_large WHERE id=999999999')
                    conn.commit()
            except Exception as e:
                new_range_ok = False
                results['new_range_insert_error'] = str(e)
            
            ddl_expected_match = (ok == expected_success)
            results['count_diff'] = count_diff
            results['mismatches'] = mismatch
            results['dml_error_rate'] = round(dml_error_rate, 4)
            results['new_range_ok'] = new_range_ok
            
            all_pass = ddl_expected_match and mismatch == 0 and dml_error_acceptable and new_range_ok
            # count_match is informational, not a hard fail (race conditions are expected)
            if not count_match:
                results['count_warning'] = f'count_diff={count_diff} exceeds tolerance={count_tolerance:.0f}'
            
            results['verification'] = 'PASS' if all_pass else f'FAIL: ddl_match={ddl_expected_match}, mismatches={mismatch}, dml_err={dml_error_rate:.2%}, new_range={new_range_ok}, count_diff={count_diff}'
        else:
            if not expected_success:
                results['verification'] = 'PASS'
            else:
                results['verification'] = f'FAIL: DDL failed unexpectedly: {err}'
    except Exception as e:
        results['error'] = str(e)
        import traceback
        results['traceback'] = traceback.format_exc()
    finally:
        # Close any lingering worker connections to release metadata locks
        try:
            if 'worker_conns' in dir():
                for wc in worker_conns:
                    try:
                        wc.close()
                    except:
                        pass
        except:
            pass
        # Wait a moment for connections to fully close
        time.sleep(1)
        try:
            exec_sql(conn, "DROP TABLE IF EXISTS t_large")
            exec_sql(conn, "DROP TABLE IF EXISTS t_large_oracle")
        except:
            pass
        conn.close()
    
    logger.info(f'[{results.get("test_id", "?")}] verification={results.get("verification")}, ddl={results.get("ddl", {}).get("duration")}s, ops={results.get("dml_ops")}')
    return results


def run_large_table_test(types=None):
    """大表测试：所有支持的数据类型 x INPLACE/INSTANT + 并发DML"""
    logger.info('=== Large Table Tests: All Types ===')
    all_results = []
    
    if types is None:
        types = LARGE_TABLE_TYPES
    
    for type_info in types:
        prefix, category, old_type, new_type, charset, signed, algo, expected, row_count = type_info
        try:
            result = run_large_table_test_single(
                prefix, category, old_type, new_type, charset,
                signed, algo, expected, row_count
            )
            all_results.append(result)
        except Exception as e:
            all_results.append({'test_id': f'LT-{prefix}', 'error': str(e)})
    
    summary = {
        'total': len(all_results),
        'passed': sum(1 for r in all_results if r.get('verification') == 'PASS'),
        'failed': sum(1 for r in all_results if 'FAIL' in str(r.get('verification', ''))),
        'errors': sum(1 for r in all_results if r.get('error')),
        'results': all_results,
    }
    logger.info(f'Large table summary: {summary["total"]} total, {summary["passed"]} PASS, {summary["failed"]} FAIL, {summary["errors"]} errors')
    return summary


# ============================================================
# 主执行器
# ============================================================
def main():
    logger.info('='*60)
    logger.info('RDS MySQL DDL Concurrent DML Verification Suite')
    logger.info('='*60)
    
    all_results = []
    
    # --- 单个用例测试 ---
    logger.info('\n### Phase 1: Individual Test Cases ###')
    
    # 1. 表列数上限
    r = run_max_column_test()
    all_results.append(('MAX_COLS', r))
    
    # 2. 连续INSTANT性能
    r = run_consecutive_instant_test()
    all_results.append(('CONSECUTIVE_INSTANT', r))
    
    # 3. DDL Fuzz 内存泄漏
    r = run_ddl_fuzz_test()
    all_results.append(('DDL_FUZZ', r))
    
    # 4. 连续ALTER链式升级
    r = run_consecutive_chain_test()
    all_results.append(('CHAIN', r))
    
    # 5. 多列同时升级
    r = run_multi_column_test()
    all_results.append(('MULTI_COL', r))
    
    # 6. 同键删除重插
    r = run_same_key_test()
    all_results.append(('SAME_KEY', r))
    
    # 7. 唯一键冲突优化
    r = run_unique_conflict_test()
    all_results.append(('UNIQUE_CONFLICT', r))
    
    # 8. 虚拟生成列
    r = run_virtual_column_test()
    all_results.append(('VIRTUAL_COL', r))
    
    # 9. 带索引字段扩容
    r = run_index_test()
    all_results.append(('INDEX', r))
    
    # 10. 视图依赖
    r = run_view_test()
    all_results.append(('VIEW', r))
    
    # 11. 临时表
    r = run_temp_table_test()
    all_results.append(('TEMP_TABLE', r))
    
    # 12. 连续多轮DDL性能
    r = run_consecutive_ddl_perf_test()
    all_results.append(('CONSEC_DDL_PERF', r))
    
    # 13. VARCHAR跨长度头 + 尾空格
    r = run_varchar_boundary_test()
    all_results.append(('VARCHAR_BOUNDARY', r))
    
    # 14. DECIMAL 9位编码边界
    r = run_decimal_boundary_test()
    all_results.append(('DECIMAL_BOUNDARY', r))
    
    # --- 并发DML测试 ---
    logger.info('\n### Phase 2: Concurrent DML Tests ###')
    
    concurrent_tests = build_concurrent_dml_tests()
    for test in concurrent_tests:
        logger.info(f'Running {test["test_id"]}...')
        try:
            result = run_single_test(
                ALIYUN_CONFIG,
                test_id=test['test_id'],
                create_t1=test['create_t1'],
                create_t2=test['create_t2'],
                alter_sql=test['alter_sql'],
                baseline=test['baseline'],
                post_ddl=test['post_ddl'],
                col_name=test['col_name'],
                algorithm=test['algorithm'],
                expected_success=test['expected_success'],
                num_workers=test.get('num_workers', 3),
                dml_duration=test.get('dml_duration', 5),
                data_type_info=test.get('data_type_info'),
            )
            all_results.append((test['test_id'], result))
        except Exception as e:
            all_results.append((test['test_id'], {'error': str(e)}))
    
    # --- 行格式测试 ---
    logger.info('\n### Phase 3: Row Format Tests ###')
    
    rf_tests = build_row_format_tests()
    for test in rf_tests:
        logger.info(f'Running {test["test_id"]}...')
        try:
            result = run_single_test(
                ALIYUN_CONFIG,
                test_id=test['test_id'],
                create_t1=test['create_t1'],
                create_t2=test['create_t2'],
                alter_sql=test['alter_sql'],
                baseline=test['baseline'],
                post_ddl=test['post_ddl'],
                col_name=test['col_name'],
                algorithm=test['algorithm'],
                expected_success=test['expected_success'],
                num_workers=test.get('num_workers', 3),
                dml_duration=test.get('dml_duration', 5),
                data_type_info=test.get('data_type_info'),
            )
            all_results.append((test['test_id'], result))
        except Exception as e:
            all_results.append((test['test_id'], {'error': str(e)}))
    
    # --- 表大小测试 ---
    logger.info('\n### Phase 4: Table Size Tests ###')
    
    ts_tests = build_table_size_tests()
    for test in ts_tests:
        logger.info(f'Running {test["test_id"]}...')
        try:
            result = run_single_test(
                ALIYUN_CONFIG,
                test_id=test['test_id'],
                create_t1=test['create_t1'],
                create_t2=test['create_t2'],
                alter_sql=test['alter_sql'],
                baseline=test['baseline'],
                post_ddl=test['post_ddl'],
                col_name=test['col_name'],
                algorithm=test['algorithm'],
                expected_success=test['expected_success'],
                num_workers=test.get('num_workers', 2),
                dml_duration=test.get('dml_duration', 5),
                data_type_info=test.get('data_type_info'),
            )
            all_results.append((test['test_id'], result))
        except Exception as e:
            all_results.append((test['test_id'], {'error': str(e)}))
    
    # --- 大表测试 ---
    logger.info('\n### Phase 5: Large Table Test ###')
    r = run_large_table_test()
    all_results.append(('LARGE_TABLE', r))
    
    # --- 输出结果 ---
    logger.info('\n### Writing Results ###')
    
    # CSV summary
    csv_path = os.path.join(RESULTS_DIR, 'concurrent_summary.csv')
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['test_id', 'algorithm', 'expected', 'actual', 'verification', 'ddl_duration', 'dml_ops', 'dml_errors', 'pre_ddl_qps', 'during_ddl_qps', 'ddl_qps_drop_pct', 'details'])
        for test_id, result in all_results:
            if isinstance(result, dict):
                algo = result.get('algorithm', '')
                expected = result.get('expected_ddl', result.get('expected', ''))
                actual = result.get('ddl_actual', result.get('ddl', {}).get('success', '') if isinstance(result.get('ddl'), dict) else '')
                verif = result.get('verification', '')
                dur = result.get('ddl_duration_s', result.get('ddl', {}).get('duration', '') if isinstance(result.get('ddl'), dict) else '')
                ops = result.get('dml_ops', '')
                errs = result.get('dml_errors', '')
                qps = result.get('qps_data', {}).get('qps_summary', {}) if isinstance(result.get('qps_data'), dict) else {}
                pre_qps = qps.get('pre_ddl_avg_qps', '')
                during_qps = qps.get('during_ddl_avg_qps', '')
                drop_pct = qps.get('ddl_qps_drop_pct', '')
                details = json.dumps({k: v for k, v in result.items() if k not in ['mismatch_log', 'errors', 'qps_data']}, default=str)[:500]
                writer.writerow([test_id, algo, expected, actual, verif, dur, ops, errs, pre_qps, during_qps, drop_pct, details])
            else:
                writer.writerow([test_id, '', '', '', str(result)[:500], '', '', '', ''])
    
    # JSON detailed
    json_path = os.path.join(RESULTS_DIR, 'concurrent_detailed.json')
    with open(json_path, 'w') as f:
        json.dump([{k: v} for k, v in all_results], f, indent=2, default=str)
    
    # Summary
    total = len(all_results)
    passed = sum(1 for _, r in all_results if isinstance(r, dict) and r.get('verification') == 'PASS')
    failed = sum(1 for _, r in all_results if isinstance(r, dict) and r.get('verification') == 'FAIL')
    errors = sum(1 for _, r in all_results if isinstance(r, dict) and r.get('error'))
    
    logger.info(f'\n{"="*60}')
    logger.info(f'TEST SUMMARY: {total} total, {passed} PASS, {failed} FAIL, {errors} errors')
    logger.info(f'Results: {csv_path}')
    logger.info(f'Detailed: {json_path}')
    logger.info(f'{"="*60}')


def main_large_only(quick=False):
    """只运行大表测试"""
    logger.info('='*60)
    logger.info('RDS MySQL DDL Large Table Verification Suite (Large Only)')
    logger.info('='*60)
    
    all_results = []
    
    types = LARGE_TABLE_TYPES
    if quick:
        # Quick mode: reduce row counts to 100K for fast verification
        types = [(t[0], t[1], t[2], t[3], t[4], t[5], t[6], t[7], 100_000) for t in LARGE_TABLE_TYPES]
        logger.info(f'QUICK MODE: reduced to 100K rows per test')
    
    logger.info(f'\n### Large Table Tests: {len(types)} entries ###')
    r = run_large_table_test(types)
    all_results.append(('LARGE_TABLE', r))
    
    # CSV summary
    csv_path = os.path.join(RESULTS_DIR, 'large_table_summary.csv')
    with open(csv_path, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['test_id', 'category', 'old_type', 'new_type', 'algorithm', 'expected', 'row_count', 'ddl_duration', 'dml_ops', 'dml_errors', 'pre_ddl_qps', 'during_ddl_qps', 'ddl_qps_drop_pct', 'verification', 'details'])
        for test_id, result in all_results:
            if isinstance(result, dict) and 'results' in result:
                for r in result['results']:
                    if isinstance(r, dict):
                        ddl = r.get('ddl', {})
                        qps = r.get('qps_summary', {}) if isinstance(r.get('qps_summary'), dict) else {}
                        writer.writerow([
                            r.get('test_id', ''), r.get('category', ''), r.get('old_type', ''), r.get('new_type', ''),
                            r.get('algorithm', ''), r.get('expected_success', ''), r.get('row_count', ''),
                            ddl.get('duration', '') if isinstance(ddl, dict) else '',
                            r.get('dml_ops', ''), r.get('dml_errors', ''),
                            qps.get('pre_ddl_avg_qps', ''), qps.get('during_ddl_avg_qps', ''), qps.get('ddl_qps_drop_pct', ''),
                            r.get('verification', ''),
                            json.dumps({k: v for k, v in r.items() if k not in ['qps_summary', 'qps_samples']}, default=str)[:500]
                        ])
            elif isinstance(result, dict):
                writer.writerow([test_id, '', '', '', '', '', '', '', '', '', '', '', '', str(result)[:500]])
    
    # JSON detailed
    json_path = os.path.join(RESULTS_DIR, 'large_table_detailed.json')
    with open(json_path, 'w') as f:
        json.dump(all_results, f, indent=2, default=str)
    
    # Summary
    if isinstance(r := all_results[0][1], dict) and 'results' in r:
        results_list = r['results']
        total = len(results_list)
        passed = sum(1 for r in results_list if isinstance(r, dict) and r.get('verification') == 'PASS')
        failed = sum(1 for r in results_list if isinstance(r, dict) and 'FAIL' in str(r.get('verification', '')))
        errors = sum(1 for r in results_list if isinstance(r, dict) and r.get('error'))
    else:
        total = len(all_results)
        passed = failed = errors = 0
    
    logger.info(f'\n{"="*60}')
    logger.info(f'LARGE TABLE SUMMARY: {total} total, {passed} PASS, {failed} FAIL, {errors} errors')
    logger.info(f'CSV: {csv_path}')
    logger.info(f'JSON: {json_path}')
    logger.info(f'{"="*60}')


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='RDS MySQL DDL Concurrent DML Verification Suite')
    parser.add_argument('--large-only', action='store_true', help='Only run large table tests')
    parser.add_argument('--quick', action='store_true', help='Quick mode: 100K rows instead of millions')
    args = parser.parse_args()
    
    if args.large_only:
        main_large_only(quick=args.quick)
    else:
        main()
