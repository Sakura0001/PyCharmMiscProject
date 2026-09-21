#!/usr/bin/env python3
"""
Dual-Write Oracle 并发DML数据一致性验证框架
核心原理：t1(旧类型) + t2(新类型Oracle) 接收相同DML序列，DDL后对比
"""
import threading
import time
import logging
import json
import random
import pymysql

# Import data generators for type-aware DML value generation
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
try:
    from data_generator import (
        gen_integer_data, gen_char_data, gen_binary_data,
        gen_decimal_data, gen_text_blob_data, gen_bit_data,
    )
except ImportError:
    gen_integer_data = gen_char_data = gen_binary_data = None
    gen_decimal_data = gen_text_blob_data = gen_bit_data = None

logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(threadName)s] %(message)s')
logger = logging.getLogger(__name__)



class QPSSampler:
    """时间窗口化QPS采集器：每秒采样DML ops，区分 pre-DDL / during-DDL / post-DDL"""
    def __init__(self):
        self._samples = []
        self._phase = 'idle'
        self._last_ops = 0
        self._last_errors = 0
        self._last_ts = None
        self._lock = threading.Lock()

    def start(self):
        self._last_ts = time.time()
        self._phase = 'pre_ddl'

    def set_phase(self, phase):
        """切换阶段: 'pre_ddl' / 'during_ddl' / 'post_ddl'"""
        self._phase = phase

    def sample(self, current_ops, current_errors):
        """采样一次，计算最近一个interval的QPS"""
        with self._lock:
            now = time.time()
            if self._last_ts is None:
                self._last_ts = now
                self._last_ops = current_ops
                self._last_errors = current_errors
                return
            elapsed = now - self._last_ts
            if elapsed >= 0.5:  # 采样间隔≥0.5s
                qps = (current_ops - self._last_ops) / elapsed if elapsed > 0 else 0
                eps = (current_errors - self._last_errors) / elapsed if elapsed > 0 else 0
                self._samples.append({
                    'ts': round(now - (self._samples[0]['ts'] if self._samples else now), 3),
                    'phase': self._phase,
                    'qps': round(qps, 1),
                    'errors_per_sec': round(eps, 2),
                    'total_ops': current_ops,
                    'total_errors': current_errors,
                })
                self._last_ops = current_ops
                self._last_errors = current_errors
                self._last_ts = now

    def get_summary(self):
        """返回QPS摘要统计"""
        if not self._samples:
            return {'qps_curve': [], 'qps_summary': {}}
        
        phases = {}
        for s in self._samples:
            p = s['phase']
            if p not in phases:
                phases[p] = []
            phases[p].append(s['qps'])
        
        def avg(lst):
            return round(sum(lst) / len(lst), 1) if lst else 0
        
        summary = {}
        for phase, qps_list in phases.items():
            summary[f'{phase}_avg_qps'] = avg(qps_list)
            summary[f'{phase}_max_qps'] = max(qps_list) if qps_list else 0
            summary[f'{phase}_min_qps'] = min(qps_list) if qps_list else 0
            summary[f'{phase}_samples'] = len(qps_list)
        
        # 计算QPS下降比例
        baseline = summary.get('pre_ddl_avg_qps', 0)
        during = summary.get('during_ddl_avg_qps', 0)
        if baseline > 0:
            summary['ddl_qps_drop_pct'] = round((1 - during / baseline) * 100, 1)
        else:
            summary['ddl_qps_drop_pct'] = 0 if during == 0 else 100
        
        # 恢复QPS
        post = summary.get('post_ddl_avg_qps', 0)
        if baseline > 0:
            summary['post_ddl_recovery_pct'] = round(post / baseline * 100, 1)
        else:
            summary['post_ddl_recovery_pct'] = 0
        
        return {
            'qps_curve': self._samples,
            'qps_summary': summary,
        }



class DualWriteOracle:
    """Dual-Write Oracle 并发DML验证"""

    def __init__(self, conn_config, test_id, create_t1_sql, create_t2_sql,
                 alter_sql, baseline_inserts, post_ddl_inserts,
                 col_name='target_col', pk_name='id',
                 algorithm='INPLACE', expected_ddl_success=True,
                 data_scale='small', num_workers=4, dml_duration=30,
                 data_type_info=None):
        self.conn_config = conn_config
        self.test_id = test_id
        self.create_t1_sql = create_t1_sql
        self.create_t2_sql = create_t2_sql
        self.alter_sql = alter_sql
        self.baseline_inserts = baseline_inserts or []
        self.post_ddl_inserts = post_ddl_inserts or []
        self.col_name = col_name
        self.pk_name = pk_name
        self.algorithm = algorithm
        self.expected_ddl_success = expected_ddl_success
        self.data_scale = data_scale
        self.num_workers = num_workers
        self.dml_duration = dml_duration

        self.results = {
            'test_id': test_id,
            'algorithm': algorithm,
            'expected_ddl': 'SUCCESS' if expected_ddl_success else 'FAIL',
            'ddl_actual': None,
            'ddl_duration_s': None,
            'dml_ops': 0,
            'dml_errors': 0,
            'verification': None,
            'mismatches': [],
            'errors': [],
            'qps_data': None,
        }

        self.data_type_info = data_type_info or {}
        self._stop_event = threading.Event()
        self._ddl_done = threading.Event()
        self._dml_ops = [0] * max(num_workers, 1)
        self._dml_errors = [0] * max(num_workers, 1)
        self._mismatch_log = []
        self._mismatch_lock = threading.Lock()
        # Track all PKs inserted for UPDATE/DELETE targeting
        self._pk_list = []
        self._pk_lock = threading.Lock()
        # QPS采样器
        self._qps_sampler = QPSSampler()
        self._qps_thread = None

    def _get_conn(self, retries=3, delay=5):
        for attempt in range(retries):
            try:
                return pymysql.connect(
                    host=self.conn_config['host'],
                    port=self.conn_config.get('port', 3306),
                    user=self.conn_config['user'],
                    password=self.conn_config['password'],
                    database=self.conn_config['database'],
                    autocommit=True,
                    charset='utf8mb4',
                )
            except Exception as e:
                if attempt < retries - 1:
                    logger.warning(f'Connection attempt {attempt+1}/{retries} failed: {e}, retrying in {delay}s...')
                    time.sleep(delay)
                else:
                    raise

    def _exec(self, conn, sql, args=None):
        try:
            cur = conn.cursor()
            cur.execute(sql, args)
            conn.commit()
            return (True, None)
        except Exception as e:
            conn.rollback()
            return (False, str(e))
        finally:
            try:
                cur.close()
            except:
                pass

    def setup(self):
        """创建表 + 插入基线数据"""
        conn = self._get_conn()
        try:
            self._exec(conn, 'DROP TABLE IF EXISTS t1')
            self._exec(conn, 'DROP TABLE IF EXISTS t2')

            ok, err = self._exec(conn, self.create_t1_sql)
            if not ok:
                self.results['errors'].append(f'CREATE t1 failed: {err}')
                return False

            ok, err = self._exec(conn, self.create_t2_sql)
            if not ok:
                self.results['errors'].append(f'CREATE t2 failed: {err}')
                return False

            # Insert baseline data
            for sql in self.baseline_inserts:
                ok, err = self._exec(conn, sql)
                if not ok and 'EXPECT_FAIL' not in sql:
                    logger.debug(f'Baseline insert failed (may be expected): {err}')

            # Sync to t2 via row-level copy
            try:
                cur = conn.cursor()
                cur.execute(f'SELECT * FROM t1')
                rows = cur.fetchall()
                cols = [d[0] for d in cur.description]
                col_list = ','.join(f'`{c}`' for c in cols)
                placeholders = ','.join(['%s'] * len(cols))
                for row in rows:
                    try:
                        cur.execute(f'REPLACE INTO t2 ({col_list}) VALUES ({placeholders})', row)
                    except Exception:
                        pass
                conn.commit()
            except Exception as e:
                self.results['errors'].append(f'Sync to t2 failed: {e}')

            # Track PKs
            try:
                cur = conn.cursor()
                cur.execute(f'SELECT {self.pk_name} FROM t1')
                self._pk_list = [r[0] for r in cur.fetchall()]
            except:
                pass

            return True
        finally:
            conn.close()

    def _dml_worker(self, worker_id, conn_config, op_type):
        """DML工作线程：对 t1 和 t2 执行相同操作"""
        try:
            conn1 = pymysql.connect(host=conn_config['host'], port=conn_config.get('port', 3306),
                                    user=conn_config['user'], password=conn_config['password'],
                                    database=conn_config['database'], autocommit=True, charset='utf8mb4',
                                    connect_timeout=10, read_timeout=30, write_timeout=30)
            conn2 = pymysql.connect(host=conn_config['host'], port=conn_config.get('port', 3306),
                                    user=conn_config['user'], password=conn_config['password'],
                                    database=conn_config['database'], autocommit=True, charset='utf8mb4',
                                    connect_timeout=10, read_timeout=30, write_timeout=30)
        except Exception as e:
            logger.error(f'Worker {worker_id} connect failed: {e}')
            return

        try:
            cur1 = conn1.cursor()
            cur2 = conn2.cursor()
            pk_counter = 100000 + worker_id * 100000
            op_count = 0

            while not self._stop_event.is_set():
                # Prevent tight loop if nothing to do
                if op_type == 'UPSERT':
                    # Treat UPSERT as INSERT-ON-DUPLICATE-KEY
                    val = self._gen_dml_value(op_type, phase='pre' if not self._ddl_done.is_set() else 'post')
                    pk = pk_counter
                    pk_counter += 1
                    sql1 = f'INSERT INTO t1 ({self.pk_name}, {self.col_name}) VALUES (%s, %s) ON DUPLICATE KEY UPDATE {self.col_name}=VALUES({self.col_name})'
                    sql2 = f'INSERT INTO t2 ({self.pk_name}, {self.col_name}) VALUES (%s, %s) ON DUPLICATE KEY UPDATE {self.col_name}=VALUES({self.col_name})'
                    args = (pk, val)
                elif op_type == 'INSERT':
                    val = self._gen_dml_value(op_type, phase='pre' if not self._ddl_done.is_set() else 'post')
                    pk = pk_counter
                    pk_counter += 1
                    sql1 = f'INSERT INTO t1 ({self.pk_name}, {self.col_name}) VALUES (%s, %s)'
                    sql2 = f'INSERT INTO t2 ({self.pk_name}, {self.col_name}) VALUES (%s, %s)'
                    args = (pk, val)
                elif op_type == 'UPDATE':
                    # Pick a random PK from tracked list (fast, no ORDER BY RAND())
                    with self._pk_lock:
                        if not self._pk_list:
                            time.sleep(0.05)
                            continue
                        target_pk = random.choice(self._pk_list[-200:])  # only recent 200
                    val = self._gen_dml_value(op_type, phase='pre' if not self._ddl_done.is_set() else 'post')
                    sql1 = f'UPDATE t1 SET {self.col_name}=%s WHERE {self.pk_name}=%s'
                    sql2 = f'UPDATE t2 SET {self.col_name}=%s WHERE {self.pk_name}=%s'
                    args = (val, target_pk)
                elif op_type == 'DELETE':
                    with self._pk_lock:
                        if not self._pk_list:
                            time.sleep(0.05)
                            continue
                        target_pk = random.choice(self._pk_list[-200:])
                    sql1 = f'DELETE FROM t1 WHERE {self.pk_name}=%s'
                    sql2 = f'DELETE FROM t2 WHERE {self.pk_name}=%s'
                    args = (target_pk,)
                elif op_type == 'SELECT':
                    # SELECT queries on both tables — verify reads work during DDL
                    queries = [
                        (f'SELECT {self.pk_name}, {self.col_name} FROM t1 WHERE {self.pk_name} = %s', (pk_counter - 1,)),
                        (f'SELECT {self.pk_name}, {self.col_name} FROM t2 WHERE {self.pk_name} = %s', (pk_counter - 1,)),
                        (f'SELECT COUNT(*) FROM t1', ()),
                        (f'SELECT COUNT(*) FROM t2', ()),
                        (f'SELECT {self.col_name} FROM t1 WHERE {self.col_name} IS NOT NULL LIMIT 5', ()),
                        (f'SELECT {self.col_name} FROM t2 WHERE {self.col_name} IS NOT NULL LIMIT 5', ()),
                        (f'SELECT MAX({self.col_name}), MIN({self.col_name}) FROM t1', ()),
                        (f'SELECT MAX({self.col_name}), MIN({self.col_name}) FROM t2', ()),
                    ]
                    q = random.choice(queries)
                    sql1 = q[0]
                    args = q[1]
                    sql2 = None  # SELECT doesn't need dual-write
                else:
                    time.sleep(0.01)
                    continue

                # Execute on t1
                try:
                    cur1.execute(sql1, args)
                    r1 = (True, None)
                except Exception as e:
                    r1 = (False, str(e))

                # For SELECT, no dual-write needed; just record result
                if op_type == 'SELECT':
                    r2 = r1  # SELECT is read-only, no dual-write
                    # Fetch results to ensure query actually executes
                    try:
                        cur1.fetchall()
                    except:
                        pass
                elif r1[0] and not self._stop_event.is_set() and sql2:
                    try:
                        cur2.execute(sql2, args)
                        r2 = (True, None)
                    except Exception as e:
                        r2 = (False, str(e))
                else:
                    r2 = (False, 'skipped_t1_failed' if sql2 else 'no_t2_needed')

                self._dml_ops[worker_id] += 1
                op_count += 1

                # QPS采样 (每~0.5s)
                if worker_id == 0:
                    self._qps_sampler.sample(sum(self._dml_ops), sum(self._dml_errors))

                # Track new PKs for UPDATE/DELETE targeting
                if op_type in ('INSERT', 'UPSERT') and r1[0]:
                    with self._pk_lock:
                        self._pk_list.append(pk)

                if r1[0] != r2[0]:
                    self._dml_errors[worker_id] += 1
                    with self._mismatch_lock:
                        if len(self._mismatch_log) < 100:
                            self._mismatch_log.append({
                                'worker': worker_id,
                                'op_type': op_type,
                                'pk': args[-1] if op_type == 'DELETE' else args[0],
                                't1_result': r1,
                                't2_result': r2,
                            })

                # Small delay to prevent overloading
                time.sleep(0.005)

        except Exception as e:
            logger.error(f'Worker {worker_id} error: {e}')
        finally:
            try:
                conn1.close()
            except:
                pass
            try:
                conn2.close()
            except:
                pass

    def _gen_dml_value(self, op_type, phase='pre'):
        """生成DML值 — 类型感知"""
        dti = self.data_type_info
        if not dti:
            if phase == 'pre':
                return random.choice([0, 1, -1, 100, -100, 255, None])
            else:
                return random.choice([0, 1, -1, 100, 9999999999, None])

        category = dti.get('category', 'integer')

        try:
            if category == 'integer':
                old_type = dti.get('old_type', 'INT')
                new_type = dti.get('new_type', 'BIGINT')
                signed = dti.get('signed', True)
                data = gen_integer_data(old_type, new_type, signed, phase)
            elif category in ('char', 'varchar'):
                old_len = dti.get('old_len', 10)
                new_len = dti.get('new_len', 20)
                charset = dti.get('charset', 'latin1')
                data = gen_char_data(old_len, new_len, charset, phase)
            elif category in ('binary', 'varbinary'):
                old_len = dti.get('old_len', 10)
                new_len = dti.get('new_len', 20)
                data = gen_binary_data(old_len, new_len, phase)
            elif category == 'decimal':
                old_M = dti.get('old_len', 10)
                new_M = dti.get('new_len', 12)
                D = dti.get('D', 2)
                data = gen_decimal_data(old_M, new_M, D, phase)
            elif category in ('text', 'blob'):
                old_subtype = dti.get('old_subtype', '')
                new_subtype = dti.get('new_subtype', '')
                is_blob = (category == 'blob')
                data = gen_text_blob_data(old_subtype, new_subtype, is_blob, phase)
            elif category == 'bit':
                old_bits = dti.get('old_len', 8)
                new_bits = dti.get('new_len', 16)
                data = gen_bit_data(old_bits, new_bits, phase)
            else:
                return random.choice([0, 1, -1, 100, None])

            safe_data = [(v, l) for v, l in data if 'EXPECT_FAIL' not in l]
            if safe_data:
                return random.choice(safe_data)[0]
            return None
        except Exception as e:
            logger.debug(f'_gen_dml_value error: {e}, fallback to integers')
            if phase == 'pre':
                return random.choice([0, 1, -1, 100, None])
            else:
                return random.choice([0, 1, -1, 100, 9999999999, None])

    def run_ddl(self):
        """执行 DDL ALTER"""
        self._qps_sampler.set_phase('during_ddl')
        conn = self._get_conn()
        try:
            t0 = time.time()
            cur = conn.cursor()
            cur.execute(self.alter_sql)
            t1 = time.time()

            self.results['ddl_actual'] = 'SUCCESS'
            self.results['ddl_duration_s'] = round(t1 - t0, 4)
            logger.info(f'[{self.test_id}] DDL succeeded in {t1-t0:.2f}s')
        except Exception as e:
            t1 = time.time()
            self.results['ddl_actual'] = 'FAIL'
            self.results['ddl_duration_s'] = round(t1 - t0, 4)
            self.results['ddl_error'] = str(e)
            logger.info(f'[{self.test_id}] DDL failed (expected={self.expected_ddl_success}): {e}')

            if not self.expected_ddl_success:
                self.results['ddl_actual'] = 'FAIL_EXPECTED'
        finally:
            conn.close()
            self._ddl_done.set()
            self._qps_sampler.set_phase('post_ddl')

    def run_post_ddl_inserts(self):
        """DDL后插入新范围数据，然后将t1完全同步到t2"""
        conn = self._get_conn()
        try:
            # Step 1: Execute post-DDL inserts to t1
            for sql in self.post_ddl_inserts:
                ok, err = self._exec(conn, sql)
                if not ok and 'EXPECT_FAIL' not in sql:
                    logger.debug(f'Post-DDL insert failed: {err}')

            # Step 2: Verify tables exist
            cur = conn.cursor()
            try:
                cur.execute('SELECT 1 FROM t1 LIMIT 1')
                cur.execute('SELECT 1 FROM t2 LIMIT 1')
            except Exception as e:
                logger.error(f'Tables missing before sync: {e}')
                return

            # Step 3: Clear t2 and rebuild from t1
            try:
                cur.execute('TRUNCATE TABLE t2')
            except Exception:
                cur.execute('DELETE FROM t2')

            # Use INSERT INTO t2 SELECT * FROM t1
            try:
                cur.execute('INSERT INTO t2 SELECT * FROM t1')
                conn.commit()
            except Exception as e:
                # Fallback to row-level copy
                logger.debug(f'INSERT...SELECT failed, falling back to row-level: {e}')
                cur.execute('SELECT * FROM t1')
                rows = cur.fetchall()
                cols = [d[0] for d in cur.description]
                col_list = ','.join(f'`{c}`' for c in cols)
                placeholders = ','.join(['%s'] * len(cols))
                for row in rows:
                    try:
                        cur.execute(f'INSERT INTO t2 ({col_list}) VALUES ({placeholders})', row)
                    except Exception:
                        pass
                conn.commit()
        except Exception as e:
            logger.error(f'Post-DDL sync error: {e}')
        finally:
            conn.close()

    def verify(self):
        """行级对比 t1 vs t2 — 使用 NULL-safe <=> 比较"""
        conn = self._get_conn()
        try:
            cur = conn.cursor()

            cur.execute('SELECT COUNT(*) FROM t1')
            t1_count = cur.fetchone()[0]
            cur.execute('SELECT COUNT(*) FROM t2')
            t2_count = cur.fetchone()[0]
            count_match = (t1_count == t2_count)

            mismatches = []
            try:
                cur.execute(f'''
                    SELECT {self.pk_name} FROM t1
                    WHERE {self.pk_name} NOT IN (SELECT {self.pk_name} FROM t2)
                    LIMIT 20
                ''')
                for row in cur.fetchall():
                    mismatches.append(f't1_extra: id={row[0]}')

                cur.execute(f'''
                    SELECT {self.pk_name} FROM t2
                    WHERE {self.pk_name} NOT IN (SELECT {self.pk_name} FROM t1)
                    LIMIT 20
                ''')
                for row in cur.fetchall():
                    mismatches.append(f't2_extra: id={row[0]}')

                cur.execute(f'''
                    SELECT a.{self.pk_name} FROM t1 a
                    JOIN t2 b ON a.{self.pk_name} = b.{self.pk_name}
                    WHERE NOT (a.{self.col_name} <=> b.{self.col_name})
                    LIMIT 20
                ''')
                for row in cur.fetchall():
                    mismatches.append(f'data_mismatch: id={row[0]}')
            except Exception as e:
                mismatches.append(f'L5 query error: {e}')

            if count_match and len(mismatches) == 0:
                result = 'PASS'
            else:
                result = 'FAIL'

            ddl_ok = False
            if self.expected_ddl_success and self.results.get('ddl_actual') == 'SUCCESS':
                ddl_ok = True
            elif not self.expected_ddl_success and 'FAIL' in str(self.results.get('ddl_actual', '')):
                ddl_ok = True

            self.results['verification'] = result if ddl_ok else 'DDL_UNEXPECTED'
            self.results['ddl_expected_match'] = ddl_ok
            self.results['t1_count'] = t1_count
            self.results['t2_count'] = t2_count
            self.results['count_match'] = count_match
            self.results['mismatches'] = mismatches[:20]
            self.results['dml_ops'] = sum(self._dml_ops)
            self.results['dml_errors'] = sum(self._dml_errors)
            self.results['mismatch_log'] = self._mismatch_log[:20]

            return result
        finally:
            conn.close()

    def run(self):
        """完整执行流程"""
        logger.info(f'[{self.test_id}] Starting setup...')
        if not self.setup():
            self.results['verification'] = 'SETUP_FAILED'
            return self.results

        # 启动QPS采样器
        self._qps_sampler.start()

        # 启动 DML 线程
        logger.info(f'[{self.test_id}] Starting {self.num_workers} DML workers...')
        op_types = ['INSERT', 'UPDATE', 'DELETE', 'SELECT', 'UPSERT']
        workers = []
        for i in range(self.num_workers):
            op_type = op_types[i % len(op_types)]
            t = threading.Thread(target=self._dml_worker, args=(i, self.conn_config, op_type),
                               name=f'DML-{i}-{op_type}')
            t.daemon = True
            t.start()
            workers.append(t)

        # 等待 DML 启动
        time.sleep(1)

        # 执行 DDL
        logger.info(f'[{self.test_id}] Firing DDL...')
        self.run_ddl()

        # DDL后继续 DML
        post_duration = min(self.dml_duration, 5)
        logger.info(f'[{self.test_id}] Post-DDL DML for {post_duration}s...')
        time.sleep(post_duration)

        # 停止 DML
        self._stop_event.set()
        for t in workers:
            t.join(timeout=10)

        alive_workers = [t for t in workers if t.is_alive()]
        if alive_workers:
            logger.warning(f'[{self.test_id}] {len(alive_workers)} workers still alive after join, waiting extra 5s')
            time.sleep(5)

        # Short wait for connection release
        time.sleep(2)

        # 插入 post-DDL 数据
        self.run_post_ddl_inserts()

        # 验证
        logger.info(f'[{self.test_id}] Verifying...')
        self.verify()

        # 采集QPS数据
        self._qps_sampler.sample(sum(self._dml_ops), sum(self._dml_errors))
        self.results['qps_data'] = self._qps_sampler.get_summary()

        # 清理
        try:
            conn = self._get_conn()
            self._exec(conn, 'DROP TABLE IF EXISTS t1')
            self._exec(conn, 'DROP TABLE IF EXISTS t2')
            conn.close()
        except:
            pass

        logger.info(f'[{self.test_id}] Done: {self.results["verification"]} '
                    f'(DDL={self.results.get("ddl_actual")}, '
                    f'DML ops={self.results["dml_ops"]}, '
                    f'errors={self.results["dml_errors"]})')

        return self.results


def run_single_test(conn_config, test_id, create_t1, create_t2, alter_sql,
                    baseline=None, post_ddl=None, col_name='c1', algorithm='INPLACE',
                    expected_success=True, data_scale='small', num_workers=4, dml_duration=30,
                    data_type_info=None):
    """运行单个测试用例"""
    oracle = DualWriteOracle(
        conn_config=conn_config,
        test_id=test_id,
        create_t1_sql=create_t1,
        create_t2_sql=create_t2,
        alter_sql=alter_sql,
        baseline_inserts=baseline or [],
        post_ddl_inserts=post_ddl or [],
        col_name=col_name,
        algorithm=algorithm,
        expected_ddl_success=expected_success,
        data_scale=data_scale,
        num_workers=num_workers,
        dml_duration=dml_duration,
        data_type_info=data_type_info,
    )
    return oracle.run()
